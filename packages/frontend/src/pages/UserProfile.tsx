/**
 * User Profile Page - Display user information and outputs
 */

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { usersAPI, outputsAPI, agreementsAPI, followAPI, User, Output } from '../lib/api';
import { useAuthStore } from '../store/authStore';
import { FollowButton } from '../components/FollowButton';

type TabType = 'outputs' | 'agreements' | 'followers' | 'following';

export function UserProfile() {
  const { username } = useParams<{ username: string }>();
  const { user: currentUser } = useAuthStore();

  const [user, setUser] = useState<User | null>(null);
  const [outputs, setOutputs] = useState<Output[]>([]);
  const [agreedOutputs, setAgreedOutputs] = useState<Output[]>([]);
  const [followers, setFollowers] = useState<User[]>([]);
  const [following, setFollowing] = useState<User[]>([]);
  const [isFollowing, setIsFollowing] = useState(false);

  const [activeTab, setActiveTab] = useState<TabType>('outputs');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const [stats, setStats] = useState({
    outputsCount: 0,
    followersCount: 0,
    followingCount: 0,
  });

  useEffect(() => {
    if (username) {
      loadUserProfile();
      loadOutputs();
    }
  }, [username]);

  useEffect(() => {
    if (username) {
      switch (activeTab) {
        case 'outputs':
          loadOutputs();
          break;
        case 'agreements':
          loadAgreedOutputs();
          break;
        case 'followers':
          loadFollowers();
          break;
        case 'following':
          loadFollowing();
          break;
      }
    }
  }, [activeTab, username]);

  const loadUserProfile = async () => {
    if (!username) return;

    setIsLoading(true);
    setError('');

    try {
      const userResponse = await usersAPI.getByUsername(username);
      setUser(userResponse.data);
      const userId = userResponse.data.id;

      // Load stats using new Follow API
      const [outputsRes, followStats] = await Promise.all([
        outputsAPI.getUserOutputs(username, 1, 0),
        followAPI.getUserStats(userId),
      ]);

      setStats({
        outputsCount: outputsRes.data.length > 0 ? 1 : 0, // This is a simplified count
        followersCount: followStats.data.follower_count,
        followingCount: followStats.data.following_count,
      });

      // Check if current user is following this user
      setIsFollowing(followStats.data.is_following);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load user profile');
    } finally {
      setIsLoading(false);
    }
  };

  const loadOutputs = async () => {
    if (!username) return;

    try {
      const response = await outputsAPI.getUserOutputs(username, 20, 0);
      setOutputs(response.data);
      setStats((prev) => ({ ...prev, outputsCount: response.data.length }));
    } catch (err) {
      console.error('Failed to load outputs:', err);
    }
  };

  const loadAgreedOutputs = async () => {
    if (!username) return;

    try {
      const response = await agreementsAPI.getUserAgreedOutputs(username, 20, 0);
      setAgreedOutputs(response.data);
    } catch (err) {
      console.error('Failed to load agreed outputs:', err);
    }
  };

  const loadFollowers = async () => {
    if (!username || !user) return;

    try {
      const response = await followAPI.getFollowers(user.id, 50, 0);
      // Note: response contains Follow objects, need to fetch user details
      // For now, simplified implementation
      setFollowers([]); // Would need to fetch user details from follower_id
      setStats((prev) => ({ ...prev, followersCount: response.data.length }));
    } catch (err) {
      console.error('Failed to load followers:', err);
    }
  };

  const loadFollowing = async () => {
    if (!username || !user) return;

    try {
      const response = await followAPI.getFollowing(user.id, 50, 0);
      // Note: response contains Follow objects, need to fetch user details
      // For now, simplified implementation
      setFollowing([]); // Would need to fetch user details from followed_id
      setStats((prev) => ({ ...prev, followingCount: response.data.length }));
    } catch (err) {
      console.error('Failed to load following:', err);
    }
  };

  // @ts-ignore - Will be used in follow button implementation
  const _handleFollowToggle = async () => {
    if (!user) return;

    try {
      if (isFollowing) {
        await followAPI.unfollowUser(user.id);
        setIsFollowing(false);
        setStats((prev) => ({ ...prev, followersCount: prev.followersCount - 1 }));
      } else {
        await followAPI.followUser(user.id);
        setIsFollowing(true);
        setStats((prev) => ({ ...prev, followersCount: prev.followersCount + 1 }));
      }
    } catch (err: any) {
      console.error('Failed to toggle follow:', err);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
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

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="mt-4 text-gray-600">Loading profile...</p>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-900 mb-2">Error</h2>
          <p className="text-red-800">{error || 'User not found'}</p>
          <Link to="/timeline" className="mt-4 inline-block text-blue-600 hover:text-blue-700 font-medium">
            ← Back to Timeline
          </Link>
        </div>
      </div>
    );
  }

  const isOwnProfile = currentUser?.username === username;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Profile Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-4">
            {/* Avatar */}
            <div className="w-20 h-20 bg-gray-300 rounded-full flex items-center justify-center text-2xl font-bold text-gray-600">
              {user.display_name.charAt(0).toUpperCase()}
            </div>

            {/* User Info */}
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{user.display_name}</h1>
              <p className="text-gray-600">@{user.username}</p>
              <p className="text-sm text-gray-500 mt-1">
                Joined {formatDate(user.created_at)}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div>
            {isOwnProfile ? (
              <Link
                to="/settings/profile"
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition text-sm font-medium"
              >
                プロフィール編集
              </Link>
            ) : (
              <FollowButton
                userId={user.id}
                initialIsFollowing={isFollowing}
                onFollowChange={(following) => {
                  setIsFollowing(following);
                  setStats((prev) => ({
                    ...prev,
                    followersCount: following ? prev.followersCount + 1 : prev.followersCount - 1,
                  }));
                }}
              />
            )}
          </div>
        </div>

        {/* Bio */}
        {user.bio && (
          <div className="mt-4">
            <p className="text-gray-700">{user.bio}</p>
          </div>
        )}

        {/* Stats */}
        <div className="mt-6 flex items-center space-x-6 text-sm">
          <button
            onClick={() => setActiveTab('outputs')}
            className="hover:text-blue-600 transition"
          >
            <span className="font-semibold text-gray-900">{stats.outputsCount}</span>
            <span className="text-gray-600 ml-1">投稿</span>
          </button>
          <button
            onClick={() => setActiveTab('followers')}
            className="hover:text-blue-600 transition"
          >
            <span className="font-semibold text-gray-900">{stats.followersCount}</span>
            <span className="text-gray-600 ml-1">フォロワー</span>
          </button>
          <button
            onClick={() => setActiveTab('following')}
            className="hover:text-blue-600 transition"
          >
            <span className="font-semibold text-gray-900">{stats.followingCount}</span>
            <span className="text-gray-600 ml-1">フォロー中</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-4 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('outputs')}
            className={`${
              activeTab === 'outputs'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            投稿 ({stats.outputsCount})
          </button>
          <button
            onClick={() => setActiveTab('agreements')}
            className={`${
              activeTab === 'agreements'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            同意
          </button>
          <button
            onClick={() => setActiveTab('followers')}
            className={`${
              activeTab === 'followers'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            フォロワー ({stats.followersCount})
          </button>
          <button
            onClick={() => setActiveTab('following')}
            className={`${
              activeTab === 'following'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            フォロー中 ({stats.followingCount})
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'outputs' && (
        <div className="space-y-4">
          {outputs.length === 0 ? (
            <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
              <p className="text-gray-600">まだ投稿がありません</p>
            </div>
          ) : (
            outputs.map((output) => (
              <div key={output.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getCategoryColor(output.category)}`}>
                      {output.category}
                    </span>
                    {output.visibility === 'private' && (
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                        🔒 Private
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-500">{formatDate(output.created_at)}</span>
                </div>

                <p className="text-gray-800 mb-4 line-clamp-3">{output.content}</p>

                {output.tags && output.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {output.tags.map((tag) => (
                      <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-md">
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}

                <Link
                  to={`/output/${output.id}`}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  View Details →
                </Link>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'agreements' && (
        <div className="space-y-4">
          {agreedOutputs.length === 0 ? (
            <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
              <p className="text-gray-600">No agreed outputs yet</p>
            </div>
          ) : (
            agreedOutputs.map((output) => (
              <div key={output.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getCategoryColor(output.category)}`}>
                      {output.category}
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                      ✓ Agreed
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">{formatDate(output.created_at)}</span>
                </div>

                <p className="text-gray-800 mb-4 line-clamp-3">{output.content}</p>

                <Link
                  to={`/output/${output.id}`}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  View Details →
                </Link>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'followers' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {followers.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-600">No followers yet</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {followers.map((follower) => (
                <div key={follower.id} className="p-4 hover:bg-gray-50 transition">
                  <Link to={`/profile/${follower.username}`} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-gray-300 rounded-full flex items-center justify-center text-lg font-bold text-gray-600">
                        {follower.display_name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{follower.display_name}</p>
                        <p className="text-sm text-gray-600">@{follower.username}</p>
                      </div>
                    </div>
                    <span className="text-blue-600 text-sm">View Profile →</span>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'following' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {following.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-600">Not following anyone yet</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {following.map((followedUser) => (
                <div key={followedUser.id} className="p-4 hover:bg-gray-50 transition">
                  <Link to={`/profile/${followedUser.username}`} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-gray-300 rounded-full flex items-center justify-center text-lg font-bold text-gray-600">
                        {followedUser.display_name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{followedUser.display_name}</p>
                        <p className="text-sm text-gray-600">@{followedUser.username}</p>
                      </div>
                    </div>
                    <span className="text-blue-600 text-sm">View Profile →</span>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
