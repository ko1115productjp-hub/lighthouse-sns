/**
 * Edit Output Page - Form for editing existing outputs
 */

import { useState, useEffect, FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { outputsAPI, Output } from '../lib/api';

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

export function EditOutput() {
  const { id } = useParams<{ id: string }>();
  const [output, setOutput] = useState<Output | null>(null);
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('other');
  const [tagsInput, setTagsInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadOutput();
  }, [id]);

  const loadOutput = async () => {
    if (!id) return;

    setIsLoading(true);
    setError('');

    try {
      const response = await outputsAPI.get(id);
      const outputData = response.data;

      setOutput(outputData);
      setContent(outputData.content);
      setCategory(outputData.category);
      setTagsInput(outputData.tags ? outputData.tags.join(', ') : '');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load output');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!id) return;

    if (content.trim().length < 10) {
      setError('Content must be at least 10 characters long');
      return;
    }

    setIsSaving(true);

    try {
      const tags = tagsInput
        .split(',')
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0);

      const response = await outputsAPI.update(id, {
        content: content.trim(),
        category,
        tags: tags.length > 0 ? tags : undefined,
      });

      const updatedOutput = response.data;

      // Navigate to the output detail page
      navigate(`/output/${updatedOutput.id}`, {
        state: { updated: true },
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update output');
    } finally {
      setIsSaving(false);
    }
  };

  const characterCount = content.length;
  const wordCount = content.trim().split(/\s+/).filter(Boolean).length;
  const hasChanges =
    content !== output?.content ||
    category !== output?.category ||
    tagsInput !== (output?.tags || []).join(', ');

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="mt-4 text-gray-600">Loading output...</p>
      </div>
    );
  }

  if (error && !output) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-900 mb-2">Error Loading Output</h2>
          <p className="text-red-800">{error}</p>
          <button
            onClick={() => navigate('/timeline')}
            className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
          >
            ← Back to Timeline
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Edit Output</h1>
        <p className="text-gray-600 mt-2">Update your output content</p>
      </div>

      {/* Output Info */}
      {output && (
        <div className="mb-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Output ID:</span>{' '}
              <span className="font-mono text-gray-900">{output.id}</span>
            </div>
            <div>
              <span className="text-gray-600">Current Version:</span>{' '}
              <span className="font-semibold text-gray-900">{output.version}</span>
            </div>
            <div>
              <span className="text-gray-600">Visibility:</span>{' '}
              <span
                className={`font-medium ${
                  output.visibility === 'public' ? 'text-green-700' : 'text-gray-700'
                }`}
              >
                {output.visibility === 'public' ? '🌐 Public' : '🔒 Private'}
              </span>
            </div>
            {output.novelty_score !== undefined && (
              <div>
                <span className="text-gray-600">Novelty Score:</span>{' '}
                <span className="font-semibold text-gray-900">
                  {(output.novelty_score * 100).toFixed(1)}%
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
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

        {/* Warning Box */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-yellow-900 mb-2">⚠️ Important Notes</h3>
          <ul className="text-sm text-yellow-800 space-y-1">
            <li>• All edits are permanently recorded in the version history</li>
            <li>• The previous version will remain accessible via hash chain</li>
            <li>• AI moderation will re-evaluate the updated content</li>
            <li>• Novelty score may be recalculated</li>
            <li>• Visibility (Public/Private) may change based on new novelty score</li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={() => navigate(`/output/${id}`)}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSaving || !hasChanges || content.trim().length < 10}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {isSaving ? 'Saving...' : hasChanges ? 'Save Changes' : 'No Changes'}
          </button>
        </div>
      </form>
    </div>
  );
}
