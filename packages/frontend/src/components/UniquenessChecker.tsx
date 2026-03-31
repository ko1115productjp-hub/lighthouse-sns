import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';

export const UniquenessChecker: React.FC<{
  content: string;
  onResult: (result: { score: number; isUnique: boolean }) => void;
}> = ({ content, onResult }) => {
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    if (!content) return;

    const checkUniqueness = async () => {
      setChecking(true);
      try {
        const response = await api.post('/posts/check-uniqueness', {
          content,
        });
        setResult(response.data);
        onResult(response.data);
      } catch (error) {
        console.error('Uniqueness check failed:', error);
      } finally {
        setChecking(false);
      }
    };

    // デバウンス（500ms）
    const timeout = setTimeout(checkUniqueness, 500);
    return () => clearTimeout(timeout);
  }, [content]);

  if (!content) return null;

  return (
    <div className="uniqueness-checker">
      {checking && <div className="checking">独自性をチェック中...</div>}

      {result && (
        <div className={result.isUnique ? 'unique' : 'not-unique'}>
          <div className="score">
            独自性スコア: {(result.score * 100).toFixed(1)}%
          </div>

          {!result.isUnique && (
            <div className="warning">
              ⚠️ この投稿は既存のコンテンツと類似しています
              {result.similarPosts && result.similarPosts.length > 0 && (
                <div className="similar-posts">
                  類似投稿:
                  {result.similarPosts.map((post: any) => (
                    <div key={post.id}>{post.content.substring(0, 50)}...</div>
                  ))}
                </div>
              )}
            </div>
          )}

          {result.isUnique && (
            <div className="success">
              ✓ この投稿は十分に独自性があります
            </div>
          )}
        </div>
      )}
    </div>
  );
};
