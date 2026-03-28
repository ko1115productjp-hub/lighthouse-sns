/**
 * Edit Profile Page - Update user profile information
 */

import { useState, useEffect, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { usersAPI } from '../lib/api';
import { useAuthStore } from '../store/authStore';

export function EditProfile() {
  const { user, checkAuth } = useAuthStore();
  const navigate = useNavigate();

  const [displayName, setDisplayName] = useState('');
  const [bio, setBio] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || '');
      setBio(user.bio || '');
    }
  }, [user]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    if (displayName.trim().length === 0) {
      setError('表示名を入力してください');
      return;
    }

    setIsLoading(true);

    try {
      await usersAPI.updateProfile({
        display_name: displayName.trim(),
        bio: bio.trim() || undefined,
      });

      // Refresh user data in store
      await checkAuth();

      setSuccess(true);

      // Navigate back to profile after a short delay
      setTimeout(() => {
        if (user) {
          navigate(`/profile/${user.username}`);
        }
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'プロフィールの更新に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    if (user) {
      navigate(`/profile/${user.username}`);
    } else {
      navigate('/timeline');
    }
  };

  const hasChanges =
    displayName !== (user?.display_name || '') || bio !== (user?.bio || '');

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">プロフィール編集</h1>
        <p className="text-gray-600 mt-2">プロフィール情報を更新する</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800">✓ プロフィールを更新しました！リダイレクト中...</p>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Username (Read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ユーザー名
            </label>
            <input
              type="text"
              value={user?.username || ''}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
            />
            <p className="mt-1 text-xs text-gray-500">ユーザー名は変更できません</p>
          </div>

          {/* Email (Read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              メールアドレス
            </label>
            <input
              type="email"
              value={user?.email || ''}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
            />
            <p className="mt-1 text-xs text-gray-500">メールアドレスは変更できません</p>
          </div>

          {/* Display Name */}
          <div>
            <label htmlFor="displayName" className="block text-sm font-medium text-gray-700 mb-2">
              表示名 *
            </label>
            <input
              id="displayName"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
              maxLength={100}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="表示名を入力"
            />
            <p className="mt-1 text-xs text-gray-500">
              {displayName.length}/100文字
            </p>
          </div>

          {/* Bio */}
          <div>
            <label htmlFor="bio" className="block text-sm font-medium text-gray-700 mb-2">
              自己紹介
            </label>
            <textarea
              id="bio"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              rows={4}
              maxLength={500}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="自己紹介を入力..."
            />
            <p className="mt-1 text-xs text-gray-500">
              {bio.length}/500文字
            </p>
          </div>

          {/* Avatar Upload - Coming Soon */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              プロフィール画像
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <div className="w-20 h-20 bg-gray-300 rounded-full mx-auto mb-3 flex items-center justify-center text-2xl font-bold text-gray-600">
                {displayName.charAt(0).toUpperCase() || 'U'}
              </div>
              <p className="text-sm text-gray-500">画像アップロード機能は近日公開予定</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={handleCancel}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={isLoading || !hasChanges}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {isLoading ? '保存中...' : hasChanges ? '変更を保存' : '変更なし'}
            </button>
          </div>
        </form>
      </div>

      {/* Account Information */}
      <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">アカウント情報</h3>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-600">ユーザーID</dt>
            <dd className="text-gray-900 font-mono text-xs">{user?.id.slice(0, 16)}...</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">アカウント作成日</dt>
            <dd className="text-gray-900">
              {user?.created_at &&
                new Date(user.created_at).toLocaleDateString('ja-JP', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
