/**
 * OutputFollowButton Component - Button for following/unfollowing specific outputs
 */

import { useState } from 'react';
import { outputFollowAPI } from '../lib/api';

interface OutputFollowButtonProps {
  outputId: string;
  initialIsFollowing: boolean;
  onFollowChange?: (isFollowing: boolean) => void;
}

export function OutputFollowButton({
  outputId,
  initialIsFollowing,
  onFollowChange,
}: OutputFollowButtonProps) {
  const [isFollowing, setIsFollowing] = useState(initialIsFollowing);
  const [isLoading, setIsLoading] = useState(false);

  const handleToggleFollow = async () => {
    setIsLoading(true);
    try {
      if (isFollowing) {
        await outputFollowAPI.unfollowOutput(outputId);
        setIsFollowing(false);
        onFollowChange?.(false);
      } else {
        await outputFollowAPI.followOutput(outputId);
        setIsFollowing(true);
        onFollowChange?.(true);
      }
    } catch (error) {
      console.error('Failed to toggle output follow:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleToggleFollow}
      disabled={isLoading}
      className={`inline-flex items-center px-3 py-1 text-sm rounded-md font-medium transition-colors ${
        isFollowing
          ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          : 'bg-green-600 text-white hover:bg-green-700'
      } disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      <svg
        className="w-4 h-4 mr-1"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        {isFollowing ? (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 13l4 4L19 7"
          />
        ) : (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        )}
      </svg>
      {isLoading ? 'Loading...' : isFollowing ? 'Following' : 'Follow Updates'}
    </button>
  );
}
