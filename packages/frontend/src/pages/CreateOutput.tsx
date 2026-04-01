/**
 * Create Output Page - Form for creating new outputs
 */

import { useState, FormEvent, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { outputsAPI, citationsAPI, Output, api } from '../lib/api';
import { ProtocolAgreementModal } from '../components/ProtocolAgreementModal';
import { EntitySearchModal, ReferencedEntity } from '../components/EntitySearchModal';

const CATEGORIES = [
  { value: 'science', label: '科学 (Science)' },
  { value: 'art', label: '芸術 (Art)' },
  { value: 'philosophy', label: '哲学 (Philosophy)' },
  { value: 'technology', label: '技術 (Technology)' },
  { value: 'society', label: '社会 (Society)' },
  { value: 'script', label: '台本 (Script)' },
  { value: 'place', label: '場所 (Place)' },
  { value: 'experience', label: '体験 (Experience)' },
  { value: 'other', label: 'その他 (Other)' },
];

export function CreateOutput() {
  const [searchParams] = useSearchParams();
  const citeOutputId = searchParams.get('cite');

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('other');
  const [tagsInput, setTagsInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const navigate = useNavigate();

  // Citation-related state
  const [citedOutput, setCitedOutput] = useState<Output | null>(null);
  const [citationType, setCitationType] = useState<'agree' | 'criticize' | 'develop' | 'reference'>('reference');
  const [citationExcerpt, setCitationExcerpt] = useState('');

  const [_isLoadingCitation, setIsLoadingCitation] = useState(false);
  // Protocol agreement state
  const [hasAgreedToProtocol, setHasAgreedToProtocol] = useState(true); // Assume true initially
  const [showProtocolModal, setShowProtocolModal] = useState(false);
  const [pendingSubmit, setPendingSubmit] = useState(false);

  // Referenced entity state (for place/book/movie reviews)
  const [referencedEntity, setReferencedEntity] = useState<ReferencedEntity | null>(null);
  const [showEntitySearch, setShowEntitySearch] = useState(false);

  // Check protocol agreement status on mount
  useEffect(() => {
    checkProtocolAgreement();
  }, []);

  // Load the output being cited
  useEffect(() => {
    if (citeOutputId) {
      loadCitedOutput(citeOutputId);
    }
  }, [citeOutputId]);

  const checkProtocolAgreement = async () => {
    try {
      const response = await api.get('/users/me/protocol-agreement');
      setHasAgreedToProtocol(response.data.has_agreed_to_protocol);
    } catch (err) {
      console.error('Failed to check protocol agreement:', err);
      // Assume not agreed if check fails
      setHasAgreedToProtocol(false);
    }
  };

  const loadCitedOutput = async (outputId: string) => {
    setIsLoadingCitation(true);
    try {
      const response = await outputsAPI.get(outputId);
      setCitedOutput(response.data);
    } catch (err) {
      console.error('Failed to load cited output:', err);
      setError('Failed to load the output you want to cite');
    } finally {
      setIsLoadingCitation(false);
    }
  };

  const handleProtocolAgree = () => {
    setHasAgreedToProtocol(true);
    setShowProtocolModal(false);

    // If there was a pending submit, proceed with creation
    if (pendingSubmit) {
      setPendingSubmit(false);
      // Re-trigger form submission by calling the submit logic
      proceedWithSubmit();
    }
  };

  const handleProtocolCancel = () => {
    setShowProtocolModal(false);
    setPendingSubmit(false);
  };

  const proceedWithSubmit = async () => {
    setError('');
    setIsLoading(true);

    try {
      const tags = tagsInput
        .split(',')
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0);

      const response = await outputsAPI.create({
        title: title.trim() || undefined,
        content: content.trim(),
        category,
        tags: tags.length > 0 ? tags : undefined,
        referenced_entity_type: referencedEntity?.type || undefined,
        referenced_entity_id: referencedEntity?.id || undefined,
        referenced_entity_data: referencedEntity?.data || undefined,
      });

      const createdOutput = response.data;

      // Check if output was rejected by AI moderation
      if (createdOutput.ai_review_status === 'rejected') {
        // Show rejection feedback
        setError(
          createdOutput.ai_review_feedback ||
            'コンテンツがモデレーションを通過しませんでした。内容を確認して編集してください。'
        );
        setIsLoading(false);
        // Don't navigate away - let user see feedback and edit
        return;
      }

      // If citing another output, create the citation
      if (citedOutput) {
        try {
          await citationsAPI.create({
            source_output_id: createdOutput.id,
            target_output_id: citedOutput.id,
            citation_type: citationType,
            excerpt: citationExcerpt.trim() || undefined,
          });
        } catch (citationErr) {
          console.error('Failed to create citation:', citationErr);
          // Don't fail the whole creation if citation fails
        }
      }

      // Navigate to the created output detail page immediately
      navigate(`/output/${createdOutput.id}`, { state: { created: true } });

      // Fire background review (don't await - runs asynchronously)
      outputsAPI.review(createdOutput.id).catch((reviewErr) => {
        console.error('Background review failed:', reviewErr);
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || '投稿の作成に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (content.trim().length < 10) {
      setError('本文は10文字以上で入力してください');
      return;
    }

    // Check if user has agreed to protocol
    if (!hasAgreedToProtocol) {
      setPendingSubmit(true);
      setShowProtocolModal(true);
      return;
    }

    // Proceed with actual submission
    await proceedWithSubmit();
  };

  const characterCount = content.length;
  const wordCount = content.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">新しい投稿を作成</h1>
        <p className="text-gray-600 mt-2">
          あなたの独自の考え、研究、創作活動をコミュニティと共有しましょう
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-red-800">
                コンテンツモデレーション
              </h3>
              <div className="mt-2 text-sm text-red-700 whitespace-pre-wrap">
                {error}
              </div>
              <div className="mt-4">
                <p className="text-xs text-red-600">
                  投稿内容を修正して、再度お試しください。
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Citation Info */}
      {citedOutput && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-sm font-semibold text-blue-900">📝 投稿を引用</h3>
            <Link
              to={`/output/${citedOutput.id}`}
              className="text-xs text-blue-600 hover:text-blue-700"
              target="_blank"
            >
              全文を表示 →
            </Link>
          </div>
          <div className="bg-white rounded p-3 mb-3">
            <p className="text-sm text-gray-700 line-clamp-3">{citedOutput.content}</p>
            <div className="mt-2 flex items-center space-x-2 text-xs text-gray-500">
              <span className="font-mono">{citedOutput.id}</span>
              <span>•</span>
              <span>{citedOutput.category}</span>
            </div>
          </div>

          {/* Citation Type */}
          <div className="mb-3">
            <label className="block text-sm font-medium text-blue-900 mb-2">
              引用の種類
            </label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { value: 'reference' as const, label: '📚 参照', desc: '情報源として引用' },
                { value: 'agree' as const, label: '✅ 同意', desc: 'このアイデアを支持' },
                { value: 'criticize' as const, label: '🔍 批判', desc: 'この作品を批評' },
                { value: 'develop' as const, label: '🚀 発展', desc: 'この上に構築' },
              ].map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setCitationType(type.value)}
                  className={`p-3 rounded-lg border-2 text-left transition ${
                    citationType === type.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-blue-300'
                  }`}
                >
                  <div className="font-medium text-sm">{type.label}</div>
                  <div className="text-xs text-gray-600 mt-1">{type.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Excerpt */}
          <div>
            <label htmlFor="excerpt" className="block text-sm font-medium text-blue-900 mb-2">
              引用箇所（任意）
            </label>
            <textarea
              id="excerpt"
              value={citationExcerpt}
              onChange={(e) => setCitationExcerpt(e.target.value)}
              rows={2}
              maxLength={500}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="引用する具体的な箇所を入力..."
            />
            <p className="mt-1 text-xs text-gray-600">
              {citationExcerpt.length}/500文字
            </p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Category Selection */}
        <div>
          <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
            カテゴリー *
          </label>
          <select
            id="category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {CATEGORIES.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            投稿に最も適したカテゴリーを選択してください
          </p>
        </div>

        {/* Title Input */}
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
            タイトル (Optional)
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={200}
            placeholder="投稿のタイトルを入力（任意）"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="mt-1 text-xs text-gray-500">
            タイトルを付けると投稿が見つけやすくなります（最大200文字）
          </p>
        </div>

        {/* Referenced Entity (Place/Book/Movie) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            場所・作品レビュー (Optional)
          </label>

          {referencedEntity ? (
            <div className="border border-green-200 bg-green-50 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">
                      {referencedEntity.type === 'place' && '🗺️'}
                      {referencedEntity.type === 'book' && '📚'}
                      {referencedEntity.type === 'movie' && '🎬'}
                    </span>
                    <h3 className="font-semibold text-gray-900">
                      {referencedEntity.data.name}
                    </h3>
                  </div>
                  {referencedEntity.type === 'place' && referencedEntity.data.address && (
                    <p className="text-sm text-gray-600">📍 {referencedEntity.data.address}</p>
                  )}
                  {referencedEntity.data.rating && (
                    <div className="flex items-center mt-2">
                      <span className="text-yellow-500">⭐</span>
                      <span className="ml-1 text-sm font-semibold">{referencedEntity.data.rating.toFixed(1)}</span>
                    </div>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => setReferencedEntity(null)}
                  className="ml-4 px-3 py-1 text-sm text-red-600 hover:text-red-700 border border-red-300 rounded-md hover:bg-red-50 transition"
                >
                  削除
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setShowEntitySearch(true)}
              className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 transition"
            >
              <span className="text-lg mr-2">📍</span>
              場所や作品を追加してレビューを書く
            </button>
          )}
          <p className="mt-2 text-xs text-gray-500">
            カフェ、レストラン、本、映画などのレビューを投稿する場合は、ここから追加できます
          </p>
        </div>

        {/* Content Editor */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label htmlFor="content" className="block text-sm font-medium text-gray-700">
              本文 *
            </label>
            <button
              type="button"
              onClick={() => setShowPreview(!showPreview)}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              {showPreview ? '編集' : 'プレビュー'}
            </button>
          </div>

          {showPreview ? (
            <div className="w-full min-h-[400px] px-4 py-3 border border-gray-300 rounded-md bg-gray-50">
              <div className="prose max-w-none">
                <p className="whitespace-pre-wrap">{content || 'プレビューする内容がありません...'}</p>
              </div>
            </div>
          ) : (
            <textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
              rows={16}
              className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="ここに投稿内容を書く... (Markdown対応)"
            />
          )}

          <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
            <p>
              {characterCount}文字、{wordCount}単語
            </p>
            <p>最低10文字必要です</p>
          </div>
        </div>

        {/* Tags Input */}
        <div>
          <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
            タグ（任意）
          </label>
          <input
            id="tags"
            type="text"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="機械学習, 哲学, 気候変動"
          />
          <p className="mt-1 text-xs text-gray-500">
            タグはカンマで区切ってください。タグを付けると他の人が投稿を見つけやすくなります。
          </p>
          {tagsInput && (
            <div className="mt-2 flex flex-wrap gap-2">
              {tagsInput.split(',').map((tag, index) => {
                const trimmedTag = tag.trim();
                return trimmedTag ? (
                  <span
                    key={index}
                    className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-md"
                  >
                    #{trimmedTag}
                  </span>
                ) : null;
              })}
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">
            📌 投稿後の流れ
          </h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• AIによるコンテンツモデレーションが行われます</li>
            <li>• 既存のコンテンツと比較して独自性スコアが計算されます</li>
            <li>
              • 高い独自性の投稿は<strong>公開</strong>（全員に表示）されます
            </li>
            <li>
              • 低い独自性の投稿は<strong>非公開</strong>（フォロワーのみに表示）されます
            </li>
            <li>• すべての編集は暗号化ハッシュにより永続的に記録されます</li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition"
          >
            キャンセル
          </button>
          <button
            type="submit"
            disabled={isLoading || content.trim().length < 10}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {isLoading ? '作成中...' : '投稿を作成'}
          </button>
        </div>
      </form>

      {/* Protocol Agreement Modal */}
      <ProtocolAgreementModal
        isOpen={showProtocolModal}
        onAgree={handleProtocolAgree}
        onCancel={handleProtocolCancel}
      />

      {/* Entity Search Modal */}
      <EntitySearchModal
        isOpen={showEntitySearch}
        onSelect={(entity) => {
          setReferencedEntity(entity);
          setShowEntitySearch(false);
        }}
        onCancel={() => setShowEntitySearch(false)}
      />
    </div>
  );
}
