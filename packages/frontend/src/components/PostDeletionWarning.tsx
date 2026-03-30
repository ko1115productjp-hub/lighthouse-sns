import React from 'react';

export const PostDeletionWarning: React.FC = () => {
  return (
    <div className="deletion-warning">
      <div className="warning-icon">⚠️</div>
      <h3>削除不可ポリシー</h3>
      <p>
        Lighthouse SNS では、一度公開された投稿は<strong>削除できません</strong>。
      </p>
      <p>
        このポリシーにより：
      </p>
      <ul>
        <li>質の高いコンテンツのみが投稿されます</li>
        <li>ユーザーは投稿に責任を持ちます</li>
        <li>長期的な信頼性が重視されます</li>
      </ul>
      <p className="note">
        例外: 法的問題や個人情報の誤掲載の場合、管理者判断で削除可能
      </p>
    </div>
  );
};

export const PostButton: React.FC<{
  onPost: () => void;
  disabled: boolean;
}> = ({ onPost, disabled }) => {
  const [confirmed, setConfirmed] = React.useState(false);

  const handleClick = () => {
    if (!confirmed) {
      setConfirmed(true);
      return;
    }

    onPost();
  };

  return (
    <div className="post-button-container">
      {confirmed && (
        <div className="confirmation">
          本当に投稿しますか？この投稿は永久に残ります。
        </div>
      )}

      <button
        onClick={handleClick}
        disabled={disabled}
        className={confirmed ? 'confirmed' : ''}
      >
        {confirmed ? '確認：投稿する' : '投稿する'}
      </button>

      {confirmed && (
        <button onClick={() => setConfirmed(false)} className="cancel">
          キャンセル
        </button>
      )}
    </div>
  );
};
