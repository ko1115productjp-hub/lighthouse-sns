# API設計書

**作成日**: 2026-03-24
**バージョン**: 1.0
**Base URL**: `https://api.sns.example.com/v1`

---

## 1. 概要

### 1.1 設計原則

- **RESTful**: リソース指向のURL設計
- **バージョニング**: URLパスに`/v1`を含める
- **一貫性**: 命名規則・レスポンス形式の統一
- **エラーハンドリング**: RFC 7807 (Problem Details)準拠
- **ページネーション**: カーソルベースページネーション
- **認証**: JWT Bearer Token

### 1.2 共通仕様

#### リクエストヘッダー
```
Authorization: Bearer {access_token}
Content-Type: application/json
Accept: application/json
```

#### レスポンス形式（成功）
```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-03-24T12:00:00Z",
    "request_id": "req_abc123"
  }
}
```

#### レスポンス形式（エラー）
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "meta": {
    "timestamp": "2026-03-24T12:00:00Z",
    "request_id": "req_abc123"
  }
}
```

#### HTTPステータスコード
- `200 OK`: 成功
- `201 Created`: リソース作成成功
- `204 No Content`: 削除成功
- `400 Bad Request`: バリデーションエラー
- `401 Unauthorized`: 認証エラー
- `403 Forbidden`: 権限エラー
- `404 Not Found`: リソース未存在
- `409 Conflict`: リソース競合
- `429 Too Many Requests`: レート制限
- `500 Internal Server Error`: サーバーエラー

#### ページネーション
```json
{
  "data": [ ... ],
  "pagination": {
    "cursor": "eyJpZCI6IjEyMyJ9",
    "has_next": true,
    "count": 20
  }
}
```

---

## 2. 認証API

### 2.1 ユーザー登録

**エンドポイント**: `POST /auth/register`

**リクエスト**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!",
  "display_name": "John Doe",
  "age_verified": true
}
```

**レスポンス** `201 Created`
```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "johndoe",
      "display_name": "John Doe",
      "created_at": "2026-03-24T12:00:00Z"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
      "expires_in": 900
    }
  }
}
```

**バリデーション**
- `email`: 有効なメール形式
- `username`: 3-50文字、英数字とアンダースコアのみ
- `password`: 8文字以上、大文字・小文字・数字を含む
- `age_verified`: 必須（18歳以上確認）

---

### 2.2 ログイン

**エンドポイント**: `POST /auth/login`

**リクエスト**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**レスポンス** `200 OK`
```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "johndoe",
      "display_name": "John Doe"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
      "expires_in": 900
    }
  }
}
```

**エラー** `401 Unauthorized`
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

---

### 2.3 トークンリフレッシュ

**エンドポイント**: `POST /auth/refresh`

**リクエスト**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**レスポンス** `200 OK`
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 900
  }
}
```

---

### 2.4 ログアウト

**エンドポイント**: `POST /auth/logout`

**リクエスト**: Authorization ヘッダーのみ

**レスポンス** `204 No Content`

---

### 2.5 パスワードリセット

**エンドポイント**: `POST /auth/reset-password`

**リクエスト**
```json
{
  "email": "user@example.com"
}
```

**レスポンス** `200 OK`
```json
{
  "data": {
    "message": "Password reset email sent"
  }
}
```

**エンドポイント**: `POST /auth/reset-password/confirm`

**リクエスト**
```json
{
  "token": "reset_token_abc123",
  "new_password": "NewSecurePass123!"
}
```

**レスポンス** `200 OK`

---

## 3. ユーザーAPI

### 3.1 自分のプロフィール取得

**エンドポイント**: `GET /users/me`

**レスポンス** `200 OK`
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "johndoe",
    "display_name": "John Doe",
    "bio": "Software engineer and philosopher",
    "avatar_url": "https://cdn.example.com/avatars/johndoe.jpg",
    "followers_count": 123,
    "following_count": 45,
    "outputs_count": 67,
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

---

### 3.2 プロフィール更新

**エンドポイント**: `PATCH /users/me`

**リクエスト**
```json
{
  "display_name": "John D.",
  "bio": "Updated bio text",
  "avatar_url": "https://cdn.example.com/avatars/new.jpg"
}
```

**レスポンス** `200 OK`
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "display_name": "John D.",
    "bio": "Updated bio text",
    "updated_at": "2026-03-24T12:00:00Z"
  }
}
```

---

### 3.3 ユーザー詳細取得

**エンドポイント**: `GET /users/:id`

**パスパラメータ**
- `id`: ユーザーID (UUID) または `username`

**レスポンス** `200 OK`
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "johndoe",
    "display_name": "John Doe",
    "bio": "Software engineer and philosopher",
    "avatar_url": "https://cdn.example.com/avatars/johndoe.jpg",
    "followers_count": 123,
    "following_count": 45,
    "outputs_count": 67,
    "is_following": false,
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

---

### 3.4 フォロー

**エンドポイント**: `POST /users/:id/follow`

**レスポンス** `201 Created`
```json
{
  "data": {
    "is_following": true,
    "followed_at": "2026-03-24T12:00:00Z"
  }
}
```

---

### 3.5 アンフォロー

**エンドポイント**: `DELETE /users/:id/follow`

**レスポンス** `204 No Content`

---

### 3.6 フォロワー一覧

**エンドポイント**: `GET /users/:id/followers`

**クエリパラメータ**
- `cursor`: ページネーションカーソル
- `limit`: 取得件数（デフォルト: 20、最大: 100）

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "id": "user_id_1",
      "username": "alice",
      "display_name": "Alice",
      "avatar_url": "https://cdn.example.com/avatars/alice.jpg",
      "followed_at": "2026-03-20T10:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6InVzZXJfaWRfMSJ9",
    "has_next": true,
    "count": 20
  }
}
```

---

### 3.7 退会（匿名化）

**エンドポイント**: `DELETE /users/me`

**リクエスト**
```json
{
  "anonymize": true,
  "password": "CurrentPassword123!"
}
```

**レスポンス** `204 No Content`

**動作**
- `anonymize=true`: ユーザー情報を匿名化（投稿は保持）
- `anonymize=false`: アカウント削除（投稿も削除） ※Phase 1では未対応

---

## 4. 投稿（Output）API

### 4.1 投稿作成

**エンドポイント**: `POST /outputs`

**リクエスト**
```json
{
  "content": "# My First Post\n\nThis is a markdown content...",
  "category": "philosophy",
  "tags": ["existentialism", "consciousness"]
}
```

**レスポンス** `201 Created`
```json
{
  "data": {
    "id": "OUT-2026-0324-A1B2C3",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "# My First Post\n\nThis is a markdown content...",
    "category": "philosophy",
    "tags": ["existentialism", "consciousness"],
    "visibility": "public",
    "ai_review_status": "pending",
    "novelty_score": null,
    "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "parent_hash": null,
    "version": 1,
    "created_at": "2026-03-24T12:00:00Z",
    "author": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "johndoe",
      "display_name": "John Doe"
    }
  }
}
```

**バリデーション**
- `content`: 1-50,000文字
- `category`: `science`, `art`, `philosophy`, `technology`, `society`, `other`
- `tags`: 最大10個、各1-30文字

---

### 4.2 投稿一覧取得

**エンドポイント**: `GET /outputs`

**クエリパラメータ**
- `cursor`: ページネーションカーソル
- `limit`: 取得件数（デフォルト: 20、最大: 100）
- `category`: カテゴリフィルタ
- `visibility`: `public` or `private`（自分の投稿のみ）
- `user_id`: 特定ユーザーの投稿のみ
- `sort`: `created_at` or `novelty_score` or `citation_count`（デフォルト: `created_at`）

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "id": "OUT-2026-0324-A1B2C3",
      "content": "# Title\n\nContent preview...",
      "category": "philosophy",
      "tags": ["tag1", "tag2"],
      "visibility": "public",
      "novelty_score": 87.5,
      "citation_count": 5,
      "agreement_count": 12,
      "created_at": "2026-03-24T12:00:00Z",
      "author": {
        "id": "user_id",
        "username": "johndoe",
        "display_name": "John Doe",
        "avatar_url": "https://cdn.example.com/avatars/johndoe.jpg"
      }
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6Ik9VVC0yMDI2LTAzMjQtQTFCMkMzIn0",
    "has_next": true,
    "count": 20
  }
}
```

---

### 4.3 投稿詳細取得

**エンドポイント**: `GET /outputs/:id`

**レスポンス** `200 OK`
```json
{
  "data": {
    "id": "OUT-2026-0324-A1B2C3",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "# My First Post\n\nFull content here...",
    "category": "philosophy",
    "tags": ["existentialism", "consciousness"],
    "visibility": "public",
    "ai_review_status": "approved",
    "novelty_score": 87.5,
    "citation_count": 5,
    "agreement_count": 12,
    "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "version": 1,
    "created_at": "2026-03-24T12:00:00Z",
    "updated_at": "2026-03-24T12:00:00Z",
    "author": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "johndoe",
      "display_name": "John Doe",
      "avatar_url": "https://cdn.example.com/avatars/johndoe.jpg"
    },
    "citations": {
      "citing_count": 3,
      "cited_count": 2
    }
  }
}
```

---

### 4.4 投稿編集

**エンドポイント**: `PATCH /outputs/:id`

**リクエスト**
```json
{
  "content": "# Updated Post\n\nUpdated content...",
  "tags": ["updated", "tags"]
}
```

**レスポンス** `200 OK`
```json
{
  "data": {
    "id": "OUT-2026-0324-A1B2C3",
    "content": "# Updated Post\n\nUpdated content...",
    "tags": ["updated", "tags"],
    "hash": "new_hash_value",
    "parent_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "version": 2,
    "updated_at": "2026-03-24T13:00:00Z"
  }
}
```

**制約**
- 著者のみ編集可能
- 編集後も履歴は保存される

---

### 4.5 編集履歴取得

**エンドポイント**: `GET /outputs/:id/history`

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "version": 2,
      "content": "# Updated Post\n\nUpdated content...",
      "hash": "new_hash",
      "parent_hash": "old_hash",
      "edited_by": {
        "id": "user_id",
        "username": "johndoe"
      },
      "created_at": "2026-03-24T13:00:00Z"
    },
    {
      "version": 1,
      "content": "# Original Post\n\nOriginal content...",
      "hash": "old_hash",
      "parent_hash": null,
      "edited_by": {
        "id": "user_id",
        "username": "johndoe"
      },
      "created_at": "2026-03-24T12:00:00Z"
    }
  ]
}
```

---

### 4.6 特定バージョン取得

**エンドポイント**: `GET /outputs/:id/history/:version`

**レスポンス** `200 OK`
```json
{
  "data": {
    "version": 1,
    "content": "# Original Post\n\nOriginal content...",
    "hash": "old_hash",
    "created_at": "2026-03-24T12:00:00Z"
  }
}
```

---

### 4.7 画像アップロード

**エンドポイント**: `POST /outputs/:id/images`

**リクエスト**: `multipart/form-data`
```
Content-Type: multipart/form-data

file: [binary image data]
```

**レスポンス** `201 Created`
```json
{
  "data": {
    "url": "https://cdn.example.com/outputs/OUT-2026-0324-A1B2C3/image_1.jpg",
    "uploaded_at": "2026-03-24T12:00:00Z"
  }
}
```

**制約**
- 最大5枚/投稿
- 各ファイル最大10MB
- 対応形式: JPEG, PNG, GIF, WebP

---

## 5. 引用（Citation）API

### 5.1 引用作成

**エンドポイント**: `POST /citations`

**リクエスト**
```json
{
  "source_output_id": "OUT-2026-0324-A1B2C3",
  "target_output_id": "OUT-2026-0320-XYZ123",
  "citation_type": "agree",
  "excerpt": "The key idea here is that..."
}
```

**レスポンス** `201 Created`
```json
{
  "data": {
    "id": "citation_id",
    "source_output_id": "OUT-2026-0324-A1B2C3",
    "target_output_id": "OUT-2026-0320-XYZ123",
    "citation_type": "agree",
    "excerpt": "The key idea here is that...",
    "created_at": "2026-03-24T12:00:00Z"
  }
}
```

**バリデーション**
- `citation_type`: `agree`, `criticize`, `develop`, `reference`
- `excerpt`: 最大500文字
- 自己引用不可（`source_output_id` != `target_output_id`の投稿者）

---

### 5.2 被引用一覧

**エンドポイント**: `GET /outputs/:id/citations`

**説明**: この投稿を引用している投稿の一覧

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "id": "citation_id",
      "source_output": {
        "id": "OUT-2026-0324-A1B2C3",
        "content": "Short preview...",
        "author": {
          "username": "johndoe",
          "display_name": "John Doe"
        }
      },
      "citation_type": "agree",
      "excerpt": "The key idea...",
      "created_at": "2026-03-24T12:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "...",
    "has_next": false,
    "count": 3
  }
}
```

---

### 5.3 引用先一覧

**エンドポイント**: `GET /outputs/:id/citing`

**説明**: この投稿が引用している投稿の一覧

**レスポンス** `200 OK`（構造は5.2と同様）

---

### 5.4 引用グラフデータ

**エンドポイント**: `GET /citations/graph/:id`

**クエリパラメータ**
- `depth`: グラフの深さ（デフォルト: 2、最大: 5）

**レスポンス** `200 OK`
```json
{
  "data": {
    "nodes": [
      {
        "id": "OUT-2026-0324-A1B2C3",
        "title": "Post Title",
        "author": "johndoe",
        "citation_count": 5
      }
    ],
    "edges": [
      {
        "source": "OUT-2026-0324-A1B2C3",
        "target": "OUT-2026-0320-XYZ123",
        "type": "agree"
      }
    ]
  }
}
```

---

## 6. 同意見（Agreement）API

### 6.1 同意見追加

**エンドポイント**: `POST /outputs/:id/agree`

**レスポンス** `201 Created`
```json
{
  "data": {
    "output_id": "OUT-2026-0324-A1B2C3",
    "agreed_at": "2026-03-24T12:00:00Z"
  }
}
```

---

### 6.2 同意見取り消し

**エンドポイント**: `DELETE /outputs/:id/agree`

**レスポンス** `204 No Content`

---

### 6.3 同意見ユーザー一覧

**エンドポイント**: `GET /outputs/:id/agreements`

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "user": {
        "id": "user_id",
        "username": "alice",
        "display_name": "Alice"
      },
      "agreed_at": "2026-03-24T10:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "...",
    "has_next": false,
    "count": 12
  }
}
```

---

## 7. 検索API

### 7.1 投稿全文検索

**エンドポイント**: `GET /search/outputs`

**クエリパラメータ**
- `q`: 検索クエリ（必須）
- `category`: カテゴリフィルタ
- `tags`: タグフィルタ（カンマ区切り）
- `date_from`: 開始日（ISO 8601）
- `date_to`: 終了日（ISO 8601）
- `min_novelty_score`: 最小新規性スコア
- `min_citation_count`: 最小引用数
- `cursor`: ページネーションカーソル
- `limit`: 取得件数

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "id": "OUT-2026-0324-A1B2C3",
      "content": "Highlighted search result...",
      "category": "philosophy",
      "novelty_score": 87.5,
      "citation_count": 5,
      "author": {
        "username": "johndoe",
        "display_name": "John Doe"
      },
      "created_at": "2026-03-24T12:00:00Z"
    }
  ],
  "pagination": {
    "cursor": "...",
    "has_next": true,
    "count": 20
  }
}
```

---

### 7.2 ユーザー検索

**エンドポイント**: `GET /search/users`

**クエリパラメータ**
- `q`: 検索クエリ（username, display_name）

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "id": "user_id",
      "username": "johndoe",
      "display_name": "John Doe",
      "avatar_url": "...",
      "followers_count": 123
    }
  ],
  "pagination": {
    "cursor": "...",
    "has_next": false,
    "count": 5
  }
}
```

---

### 7.3 タグ検索

**エンドポイント**: `GET /search/tags`

**クエリパラメータ**
- `tag`: タグ名（必須）

**レスポンス** `200 OK`（構造は7.1と同様）

---

## 8. フィードAPI

### 8.1 タイムラインフィード

**エンドポイント**: `GET /feed/timeline`

**説明**: フォロー中ユーザーの投稿を時系列表示

**クエリパラメータ**
- `cursor`: ページネーションカーソル
- `limit`: 取得件数

**レスポンス** `200 OK`（構造は4.2と同様）

---

### 8.2 サジェストフィード（Phase 2）

**エンドポイント**: `GET /feed/suggested`

**説明**: 引用数・新規性スコアに基づくサジェスト

**クエリパラメータ**
- `category`: カテゴリフィルタ
- `cursor`: ページネーションカーソル
- `limit`: 取得件数

**レスポンス** `200 OK`（構造は4.2と同様）

---

### 8.3 トレンドフィード

**エンドポイント**: `GET /feed/trending`

**説明**: 直近24時間の引用数ランキング

**クエリパラメータ**
- `period`: `daily`, `weekly`, `monthly`（デフォルト: `daily`）
- `limit`: 取得件数（最大100）

**レスポンス** `200 OK`（構造は4.2と同様）

---

## 9. ハッシュ検証API（公開）

### 9.1 ハッシュチェーン検証

**エンドポイント**: `GET /verify/hash/:output_id`

**説明**: 投稿のハッシュチェーン整合性を検証

**レスポンス** `200 OK`
```json
{
  "data": {
    "output_id": "OUT-2026-0324-A1B2C3",
    "stored_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "calculated_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "is_valid": true,
    "verified_at": "2026-03-24T12:00:00Z"
  }
}
```

---

### 9.2 アンカリング履歴（Phase 3）

**エンドポイント**: `GET /anchors`

**クエリパラメータ**
- `date_from`: 開始日
- `date_to`: 終了日

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "id": "anchor_id",
      "root_hash": "abc123...",
      "blockchain": "bitcoin",
      "transaction_id": "tx_abc123",
      "anchored_at": "2026-03-24T03:00:00Z",
      "explorer_url": "https://blockstream.info/tx/tx_abc123"
    }
  ]
}
```

---

## 10. NFT API（Phase 3）

### 10.1 NFT発行

**エンドポイント**: `POST /outputs/:id/nft`

**リクエスト**
```json
{
  "blockchain": "polygon",
  "recipient_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

**レスポンス** `201 Created`
```json
{
  "data": {
    "token_id": 1,
    "contract_address": "0x123...",
    "blockchain": "polygon",
    "ipfs_hash": "QmXXX...",
    "metadata_url": "ipfs://QmXXX.../metadata.json",
    "transaction_hash": "0xabc123...",
    "opensea_url": "https://opensea.io/assets/polygon/0x123.../1",
    "minted_at": "2026-03-24T12:00:00Z"
  }
}
```

**制約**
- Public Outputのみ
- 新規性スコア >= 80
- 著者のみ発行可能

---

### 10.2 NFT一覧取得

**エンドポイント**: `GET /outputs/:id/nft`

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "token_id": 1,
      "contract_address": "0x123...",
      "blockchain": "polygon",
      "owner_address": "0x742...",
      "minted_at": "2026-03-24T12:00:00Z"
    }
  ]
}
```

---

## 11. Kindle出版API（Phase 3）

### 11.1 EPUB生成

**エンドポイント**: `POST /outputs/:id/epub`

**リクエスト**
```json
{
  "output_ids": [
    "OUT-2026-0324-A1B2C3",
    "OUT-2026-0325-DEF456"
  ],
  "title": "My Collection",
  "author_name": "John Doe",
  "cover_image_url": "https://cdn.example.com/cover.jpg"
}
```

**レスポンス** `201 Created`
```json
{
  "data": {
    "epub_url": "https://cdn.example.com/epub/collection_abc123.epub",
    "generated_at": "2026-03-24T12:00:00Z",
    "metadata": {
      "title": "My Collection",
      "author": "John Doe",
      "page_count": 120
    }
  }
}
```

---

### 11.2 Kindle出版ステータス

**エンドポイント**: `GET /outputs/:id/kindle/status`

**レスポンス** `200 OK`
```json
{
  "data": {
    "status": "published",
    "asin": "B09XYZ123",
    "kindle_url": "https://www.amazon.com/dp/B09XYZ123",
    "published_at": "2026-03-25T00:00:00Z"
  }
}
```

---

## 12. WebSocket API（リアルタイム通知）

### 12.1 接続

**エンドポイント**: `wss://api.sns.example.com/v1/ws`

**認証**: クエリパラメータに`token={access_token}`

### 12.2 イベント形式

**AI査読完了通知**
```json
{
  "event": "ai_review_completed",
  "data": {
    "output_id": "OUT-2026-0324-A1B2C3",
    "status": "approved",
    "novelty_score": 87.5,
    "visibility": "public"
  },
  "timestamp": "2026-03-24T12:00:00Z"
}
```

**新規引用通知**
```json
{
  "event": "new_citation",
  "data": {
    "citation_id": "citation_id",
    "source_output_id": "OUT-2026-0324-XYZ",
    "target_output_id": "OUT-2026-0320-ABC",
    "citation_type": "agree",
    "author": {
      "username": "alice",
      "display_name": "Alice"
    }
  },
  "timestamp": "2026-03-24T12:00:00Z"
}
```

**新規フォロワー通知**
```json
{
  "event": "new_follower",
  "data": {
    "follower": {
      "id": "user_id",
      "username": "bob",
      "display_name": "Bob"
    }
  },
  "timestamp": "2026-03-24T12:00:00Z"
}
```

---

## 13. レート制限

| エンドポイント | 制限 | 単位 |
|--------------|------|------|
| `POST /auth/login` | 5回 | 5分/IP |
| `POST /outputs` | 10回 | 1時間/ユーザー |
| `POST /citations` | 50回 | 1時間/ユーザー |
| `GET /search/*` | 30回 | 1分/ユーザー |
| その他GETエンドポイント | 100回 | 1分/ユーザー |
| その他POSTエンドポイント | 60回 | 1分/ユーザー |

**レート制限超過時のレスポンス** `429 Too Many Requests`
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Try again in 30 seconds.",
    "retry_after": 30
  }
}
```

---

## 14. エラーコード一覧

| コード | HTTPステータス | 説明 |
|--------|--------------|------|
| `VALIDATION_ERROR` | 400 | バリデーションエラー |
| `INVALID_CREDENTIALS` | 401 | 認証エラー |
| `TOKEN_EXPIRED` | 401 | トークン期限切れ |
| `FORBIDDEN` | 403 | 権限不足 |
| `NOT_FOUND` | 404 | リソース未存在 |
| `CONFLICT` | 409 | リソース競合（重複等） |
| `RATE_LIMIT_EXCEEDED` | 429 | レート制限超過 |
| `AI_REVIEW_FAILED` | 500 | AI査読処理失敗 |
| `INTERNAL_ERROR` | 500 | サーバー内部エラー |

---

## 15. 変更履歴

| バージョン | 日付 | 変更内容 | 著者 |
|-----------|------|---------|------|
| 1.0 | 2026-03-24 | 初版作成 | - |
