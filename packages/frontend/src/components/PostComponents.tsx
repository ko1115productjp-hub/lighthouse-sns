import React from 'react';
import { api } from '../services/api';

interface Post {
  id: string;
  content: string;
  userId: string;
  createdAt: string;
  uniquenessScore: number;
}

export const PostList: React.FC = () => {
  const [posts, setPosts] = React.useState<Post[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/posts');
      setPosts(response.data);
      setError(null);
    } catch (err) {
      setError('投稿の取得に失敗しました');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">読み込み中...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="post-list">
      <h2>投稿一覧</h2>

      {posts.length === 0 ? (
        <div className="empty">投稿がありません</div>
      ) : (
        <div className="posts">
          {posts.map((post) => (
            <div key={post.id} className="post-item">
              <div className="post-content">{post.content}</div>
              <div className="post-meta">
                <span className="uniqueness-badge">
                  独自性: {(post.uniquenessScore * 100).toFixed(1)}%
                </span>
                <span className="timestamp">
                  {new Date(post.createdAt).toLocaleString('ja-JP')}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export const CreatePostForm: React.FC<{ onSuccess: () => void }> = ({ onSuccess }) => {
  const [content, setContent] = React.useState('');
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!content.trim()) {
      setError('投稿内容を入力してください');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      await api.post('/posts', { content });

      setContent('');
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.message || '投稿に失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="create-post-form">
      <h3>新しい投稿</h3>

      {error && <div className="error">{error}</div>}

      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="独自性のあるコンテンツを投稿してください..."
        rows={5}
        disabled={submitting}
        className="post-textarea"
      />

      <button type="submit" disabled={submitting || !content.trim()}>
        {submitting ? '投稿中...' : '投稿する'}
      </button>

      <div className="hint">
        ※ この投稿は削除できません。慎重に入力してください。
      </div>
    </form>
  );
};
