/**
 * Entity Search Modal - Search for places, books, movies, etc.
 */

import { useState } from 'react';
import { api } from '../lib/api';

export interface ReferencedEntity {
  type: 'place' | 'book' | 'movie' | 'stage' | 'concert';
  id: string;
  data: any;
}

interface EntitySearchModalProps {
  isOpen: boolean;
  onSelect: (entity: ReferencedEntity) => void;
  onCancel: () => void;
}

interface PlaceSearchResult {
  place_id: string;
  name: string;
  address: string;
  lat?: number;
  lng?: number;
  rating?: number;
  types?: string[];
}

export function EntitySearchModal({ isOpen, onSelect, onCancel }: EntitySearchModalProps) {
  const [entityType, setEntityType] = useState<'place' | 'book' | 'movie' | 'stage' | 'concert'>('place');
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<PlaceSearchResult[]>([]);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setIsSearching(true);
    setError('');
    setSearchResults([]);

    try {
      if (entityType === 'place') {
        const response = await api.post('/places/search', {
          query: searchQuery,
        });
        setSearchResults(response.data);
      } else {
        // TODO: Implement book, movie, stage, concert search
        setError(`${entityType} search not implemented yet`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to search');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectPlace = async (place: PlaceSearchResult) => {
    try {
      // Fetch detailed information
      const response = await api.get(`/places/${place.place_id}`);
      const placeDetails = response.data;

      onSelect({
        type: 'place',
        id: place.place_id,
        data: placeDetails,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch place details');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            📍 Add Place or Media Review
          </h2>

          {/* Entity Type Selection */}
          <div className="grid grid-cols-5 gap-2 mb-4">
            {[
              { value: 'place' as const, label: '🗺️ 場所', available: true },
              { value: 'book' as const, label: '📚 本', available: false },
              { value: 'movie' as const, label: '🎬 映画', available: false },
              { value: 'stage' as const, label: '🎭 舞台', available: false },
              { value: 'concert' as const, label: '🎵 ライブ', available: false },
            ].map((type) => (
              <button
                key={type.value}
                type="button"
                onClick={() => setEntityType(type.value)}
                disabled={!type.available}
                className={`p-3 rounded-lg border-2 text-center transition ${
                  entityType === type.value
                    ? 'border-blue-500 bg-blue-50'
                    : type.available
                    ? 'border-gray-200 bg-white hover:border-blue-300'
                    : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-50'
                }`}
              >
                <div className="text-sm font-medium">{type.label}</div>
                {!type.available && (
                  <div className="text-xs text-gray-500 mt-1">Coming Soon</div>
                )}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                entityType === 'place'
                  ? 'カフェ 渋谷、レストラン 表参道、など...'
                  : '検索キーワードを入力...'
              }
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSearch}
              disabled={isSearching || !searchQuery.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {isSearching ? '検索中...' : '検索'}
            </button>
          </div>
        </div>

        {/* Search Results */}
        <div className="p-6 overflow-y-auto flex-1">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {searchResults.length > 0 ? (
            <div className="space-y-3">
              <p className="text-sm text-gray-600 mb-3">
                {searchResults.length} 件の結果が見つかりました
              </p>
              {searchResults.map((place) => (
                <button
                  key={place.place_id}
                  onClick={() => handleSelectPlace(place)}
                  className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{place.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">{place.address}</p>
                      {place.types && place.types.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {place.types.slice(0, 3).map((type, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                            >
                              {type}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    {place.rating && (
                      <div className="ml-4 flex items-center text-yellow-500">
                        <span className="text-lg">⭐</span>
                        <span className="ml-1 font-semibold">{place.rating.toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>
          ) : isSearching ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">検索中...</p>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <p>検索キーワードを入力して検索してください</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onCancel}
            className="w-full px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-100 transition"
          >
            キャンセル
          </button>
        </div>
      </div>
    </div>
  );
}
