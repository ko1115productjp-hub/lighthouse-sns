/**
 * Timeline Page - Main feed of outputs
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { outputsAPI, Output } from '../lib/api';

export function Timeline() {
  const [outputs, setOutputs] = useState<Output[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<'all' | 'public' | 'private'>('all');

  useEffect(() => {
    loadOutputs();
  }, [filter]);

  const loadOutputs = async () => {
    setIsLoading(true);
    setError('');
    try {
      const visibility = filter === 'all' ? undefined : filter;
      const response = await outputsAPI.getTimeline(20, 0, visibility);
      setOutputs(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load timeline');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      science: 'bg-blue-100 text-blue-800',
      art: 'bg-purple-100 text-purple-800',
      philosophy: 'bg-green-100 text-green-800',
      technology: 'bg-yellow-100 text-yellow-800',
      society: 'bg-red-100 text-red-800',
      script: 'bg-pink-100 text-pink-800',
      place: 'bg-teal-100 text-teal-800',
      experience: 'bg-orange-100 text-orange-800',
      other: 'bg-gray-100 text-gray-800',
    };
    return colors[category] || colors.other;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Timeline</h1>
        <p className="text-gray-600 mt-2">Explore academic outputs from the community</p>
      </div>

      {/* Filter Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setFilter('all')}
            className={`${
              filter === 'all'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            All Outputs
          </button>
          <button
            onClick={() => setFilter('public')}
            className={`${
              filter === 'public'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Public Only
          </button>
          <button
            onClick={() => setFilter('private')}
            className={`${
              filter === 'private'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Private (Following)
          </button>
        </nav>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading outputs...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && outputs.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-600">No outputs to display</p>
          <Link
            to="/create"
            className="inline-block mt-4 text-blue-600 hover:text-blue-700 font-medium"
          >
            Create your first output
          </Link>
        </div>
      )}

      {/* Outputs List */}
      {!isLoading && !error && outputs.length > 0 && (
        <div className="space-y-4">
          {outputs.map((output) => (
            <div key={output.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-300 rounded-full"></div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">User #{output.user_id.slice(0, 8)}</p>
                    <p className="text-xs text-gray-500">{formatDate(output.created_at)}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(
                      output.category
                    )}`}
                  >
                    {output.category}
                  </span>
                  {output.visibility === 'private' && (
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                      🔒 Private
                    </span>
                  )}
                  {output.novelty_score !== undefined && output.novelty_score >= 0.5 && (
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                      ✨ High Novelty
                    </span>
                  )}
                </div>
              </div>

              {/* Content */}
              <div className="mb-4">
                <p className="text-gray-800 whitespace-pre-wrap">
                  {output.content.length > 500
                    ? output.content.substring(0, 500) + '...'
                    : output.content}
                </p>
              </div>

              {/* Tags */}
              {output.tags && output.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {output.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-md"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Footer */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>Version {output.version}</span>
                  <span>ID: {output.id}</span>
                </div>
                <Link
                  to={`/output/${output.id}`}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  View Details →
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
