/**
 * Create Output Page - Form for creating new outputs
 */

import { useState, FormEvent, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { outputsAPI, citationsAPI, Output } from '../lib/api';

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
  const [isLoadingCitation, setIsLoadingCitation] = useState(false);

  // Load the output being cited
  useEffect(() => {
    if (citeOutputId) {
      loadCitedOutput(citeOutputId);
    }
  }, [citeOutputId]);

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

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (content.trim().length < 10) {
      setError('Content must be at least 10 characters long');
      return;
    }

    setIsLoading(true);

    try {
      const tags = tagsInput
        .split(',')
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0);

      const response = await outputsAPI.create({
        content: content.trim(),
        category,
        tags: tags.length > 0 ? tags : undefined,
      });

      const createdOutput = response.data;

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

      // Navigate to the created output detail page
      navigate(`/output/${createdOutput.id}`, {
        state: { noveltyScore: createdOutput.novelty_score },
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create output');
    } finally {
      setIsLoading(false);
    }
  };

  const characterCount = content.length;
  const wordCount = content.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Create New Output</h1>
        <p className="text-gray-600 mt-2">
          Share your thoughts, research, or creative work with the community
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Citation Info */}
      {citedOutput && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-sm font-semibold text-blue-900">📝 Citing Output</h3>
            <Link
              to={`/output/${citedOutput.id}`}
              className="text-xs text-blue-600 hover:text-blue-700"
              target="_blank"
            >
              View Full Output →
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
              Citation Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { value: 'reference' as const, label: '📚 Reference', desc: 'Citing as source' },
                { value: 'agree' as const, label: '✅ Agree', desc: 'Supporting this idea' },
                { value: 'criticize' as const, label: '🔍 Criticize', desc: 'Critiquing this work' },
                { value: 'develop' as const, label: '🚀 Develop', desc: 'Building upon this' },
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
              Excerpt (Optional)
            </label>
            <textarea
              id="excerpt"
              value={citationExcerpt}
              onChange={(e) => setCitationExcerpt(e.target.value)}
              rows={2}
              maxLength={500}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="Quote a specific part you're citing..."
            />
            <p className="mt-1 text-xs text-gray-600">
              {citationExcerpt.length}/500 characters
            </p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Category Selection */}
        <div>
          <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
            Category *
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
            Select the most appropriate category for your output
          </p>
        </div>

        {/* Content Editor */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label htmlFor="content" className="block text-sm font-medium text-gray-700">
              Content *
            </label>
            <button
              type="button"
              onClick={() => setShowPreview(!showPreview)}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              {showPreview ? 'Edit' : 'Preview'}
            </button>
          </div>

          {showPreview ? (
            <div className="w-full min-h-[400px] px-4 py-3 border border-gray-300 rounded-md bg-gray-50">
              <div className="prose max-w-none">
                <p className="whitespace-pre-wrap">{content || 'Nothing to preview...'}</p>
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
              placeholder="Write your output here... (Markdown supported)"
            />
          )}

          <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
            <p>
              {characterCount} characters, {wordCount} words
            </p>
            <p>Minimum 10 characters required</p>
          </div>
        </div>

        {/* Tags Input */}
        <div>
          <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
            Tags (Optional)
          </label>
          <input
            id="tags"
            type="text"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="machine-learning, philosophy, climate-change"
          />
          <p className="mt-1 text-xs text-gray-500">
            Separate tags with commas. Tags help others discover your output.
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
            📌 What happens after you submit?
          </h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Your output will be analyzed by AI for content moderation</li>
            <li>• A novelty score will be calculated based on existing content</li>
            <li>
              • High novelty outputs become <strong>Public</strong> (visible to everyone)
            </li>
            <li>
              • Lower novelty outputs become <strong>Private</strong> (visible to followers)
            </li>
            <li>• All edits are permanently recorded with cryptographic hashing</li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading || content.trim().length < 10}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {isLoading ? 'Creating...' : 'Create Output'}
          </button>
        </div>
      </form>
    </div>
  );
}
