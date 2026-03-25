# システムアーキテクチャ設計書

**作成日**: 2026-03-24
**バージョン**: 1.0

---

## 1. アーキテクチャ概要

### 1.1 全体構成

```
┌─────────────────────────────────────────────────────────────┐
│                         User Layer                           │
│  (Web Browser / Mobile Browser)                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                          CDN Layer                           │
│  (Cloudflare - Static Assets, DDoS Protection)              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React SPA)                     │
│  - TypeScript + React + Vite                                │
│  - Tailwind CSS + shadcn/ui                                 │
│  - Hosted on Cloud Run / Vercel                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓ REST API / WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                         │
│  (Cloud Load Balancer + API Rate Limiting)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │        Backend API (FastAPI + Python)                 │  │
│  │  - User Management                                    │  │
│  │  - Output (Post) CRUD                                 │  │
│  │  - Citation Management                                │  │
│  │  - Hash Chain Verification                            │  │
│  │  - Search & Discovery                                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │     AI Review Service (Async Worker - Celery)         │  │
│  │  - Content Moderation (OpenAI Moderation)             │  │
│  │  - Novelty Detection (Phase 2)                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   Anchoring Service (Phase 3 - Scheduled Batch)       │  │
│  │  - Daily Root Hash → Bitcoin/OpenTimestamps           │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │     NFT Service (Phase 3 - Blockchain Integration)    │  │
│  │  - Mint NFT (ERC-721/1155)                            │  │
│  │  - Metadata Upload to IPFS                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Redis     │  │  Pinecone    │      │
│  │   (Main DB)  │  │   (Cache)    │  │ (Vector DB)  │      │
│  │              │  │              │  │  (Phase 2)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  Cloud       │  │     IPFS     │                        │
│  │  Storage     │  │  (Phase 3)   │                        │
│  │  (S3/GCS)    │  │              │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
│  - OpenAI API (Moderation, Embeddings)                      │
│  - Supabase Auth (Authentication)                           │
│  - SendGrid (Email)                                         │
│  - OpenTimestamps / Bitcoin (Anchoring)                     │
│  - Polygon Network (NFT Minting)                            │
│  - Kindle Direct Publishing (EPUB Export)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. レイヤー詳細設計

### 2.1 Frontend Layer

#### 構成
- **Framework**: React 18 + TypeScript
- **Routing**: React Router v6
- **State Management**: Zustand (グローバル状態)、React Query (サーバー状態)
- **UI Components**: shadcn/ui (Radix UI ベース)

#### ディレクトリ構造
```
frontend/
├── src/
│   ├── app/               # ルートコンポーネント
│   ├── pages/             # ページコンポーネント
│   │   ├── auth/          # 認証関連
│   │   ├── output/        # 投稿関連
│   │   ├── citation/      # 引用グラフ
│   │   └── profile/       # プロフィール
│   ├── components/        # 再利用可能コンポーネント
│   │   ├── ui/            # shadcn/ui コンポーネント
│   │   ├── editor/        # Markdownエディタ
│   │   └── graph/         # 引用グラフ可視化
│   ├── hooks/             # カスタムフック
│   ├── lib/               # ユーティリティ
│   ├── services/          # API クライアント
│   └── stores/            # Zustand ストア
├── public/
└── package.json
```

#### 主要機能モジュール
1. **AuthModule**: JWT管理、ログイン状態保持
2. **OutputModule**: 投稿CRUD、Markdownエディタ
3. **CitationModule**: 引用作成、グラフ可視化
4. **HistoryModule**: 編集履歴、diff表示
5. **SearchModule**: 全文検索、フィルタ

---

### 2.2 Backend API Layer

#### 構成
- **Framework**: FastAPI 0.110+
- **ORM**: SQLAlchemy 2.x (async)
- **Migration**: Alembic
- **Validation**: Pydantic v2

#### ディレクトリ構造
```
backend/
├── app/
│   ├── main.py            # FastAPI app エントリポイント
│   ├── config.py          # 環境変数・設定
│   ├── database.py        # DB接続設定
│   ├── dependencies.py    # 依存性注入
│   ├── models/            # SQLAlchemy モデル
│   │   ├── user.py
│   │   ├── output.py
│   │   ├── citation.py
│   │   └── hash_anchor.py
│   ├── schemas/           # Pydantic スキーマ
│   │   ├── user.py
│   │   ├── output.py
│   │   └── citation.py
│   ├── routers/           # エンドポイント定義
│   │   ├── auth.py        # 認証API
│   │   ├── users.py       # ユーザーAPI
│   │   ├── outputs.py     # 投稿API
│   │   ├── citations.py   # 引用API
│   │   └── search.py      # 検索API
│   ├── services/          # ビジネスロジック
│   │   ├── hash_chain.py  # ハッシュチェーン
│   │   ├── ai_review.py   # AI査読
│   │   ├── novelty.py     # 新規性判定 (Phase 2)
│   │   └── nft.py         # NFT発行 (Phase 3)
│   ├── workers/           # Celery タスク
│   │   ├── ai_review_worker.py
│   │   ├── anchoring_worker.py
│   │   └── nft_worker.py
│   └── utils/             # ユーティリティ
│       ├── security.py    # JWT, パスワードハッシュ
│       ├── hash.py        # SHA-256ハッシュ
│       └── pagination.py
├── tests/
├── alembic/               # マイグレーション
└── pyproject.toml
```

#### APIエンドポイント設計（Phase 1）

**認証**
```
POST   /api/v1/auth/register          # ユーザー登録
POST   /api/v1/auth/login             # ログイン
POST   /api/v1/auth/refresh           # トークンリフレッシュ
POST   /api/v1/auth/logout            # ログアウト
POST   /api/v1/auth/reset-password    # パスワードリセット
```

**ユーザー**
```
GET    /api/v1/users/me               # 自分のプロフィール
PATCH  /api/v1/users/me               # プロフィール更新
DELETE /api/v1/users/me               # 退会（匿名化）
GET    /api/v1/users/:id              # ユーザー詳細
POST   /api/v1/users/:id/follow       # フォロー
DELETE /api/v1/users/:id/follow       # アンフォロー
GET    /api/v1/users/:id/followers    # フォロワー一覧
GET    /api/v1/users/:id/following    # フォロー中一覧
```

**投稿（Output）**
```
POST   /api/v1/outputs                # 投稿作成
GET    /api/v1/outputs                # 投稿一覧（ページネーション）
GET    /api/v1/outputs/:id            # 投稿詳細
PATCH  /api/v1/outputs/:id            # 投稿編集
GET    /api/v1/outputs/:id/history    # 編集履歴
GET    /api/v1/outputs/:id/history/:version  # 特定バージョン
POST   /api/v1/outputs/:id/images     # 画像アップロード
```

**引用（Citation）**
```
POST   /api/v1/citations              # 引用作成
GET    /api/v1/outputs/:id/citations  # 被引用一覧
GET    /api/v1/outputs/:id/citing     # この投稿が引用している一覧
GET    /api/v1/citations/graph/:id    # 引用グラフデータ
```

**同意見（Agreement）**
```
POST   /api/v1/outputs/:id/agree      # 同意見追加
DELETE /api/v1/outputs/:id/agree      # 同意見取り消し
GET    /api/v1/outputs/:id/agreements # 同意見一覧
```

**検索**
```
GET    /api/v1/search/outputs?q=...   # 投稿全文検索
GET    /api/v1/search/users?q=...     # ユーザー検索
GET    /api/v1/search/tags?tag=...    # タグ検索
```

**フィード**
```
GET    /api/v1/feed/timeline          # タイムライン（フォロー中）
GET    /api/v1/feed/suggested         # サジェストフィード（Phase 2）
GET    /api/v1/feed/trending          # トレンド（引用数ランキング）
```

**ハッシュ検証（公開API）**
```
GET    /api/v1/verify/hash/:output_id # ハッシュチェーン検証
GET    /api/v1/anchors                # アンカリング履歴（Phase 3）
```

---

### 2.3 Data Layer

#### 2.3.1 PostgreSQL スキーマ設計

**users テーブル**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    bio TEXT,
    age_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    password_hash VARCHAR(255),  -- NULL if social login
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,  -- 匿名化時にタイムスタンプ
    INDEX idx_username (username),
    INDEX idx_email (email)
);
```

**outputs テーブル**
```sql
CREATE TABLE outputs (
    id VARCHAR(30) PRIMARY KEY,  -- OUT-2026-0324-A1B2C3
    user_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    category VARCHAR(50),
    tags TEXT[],  -- PostgreSQL配列
    visibility VARCHAR(10) DEFAULT 'public',  -- public/private
    novelty_score FLOAT,  -- 0-100 (Phase 2)
    ai_review_status VARCHAR(20) DEFAULT 'pending',  -- pending/approved/rejected
    hash VARCHAR(64) NOT NULL,  -- SHA-256
    parent_hash VARCHAR(64),  -- 前バージョンのハッシュ（編集時）
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_visibility (visibility),
    INDEX idx_created_at (created_at),
    INDEX idx_novelty_score (novelty_score)
);

-- Full-text search インデックス
CREATE INDEX idx_outputs_content_fts ON outputs USING GIN (to_tsvector('english', content));
```

**output_history テーブル**
```sql
CREATE TABLE output_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    output_id VARCHAR(30) REFERENCES outputs(id),
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    edited_by UUID REFERENCES users(id),
    hash VARCHAR(64) NOT NULL,
    parent_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(output_id, version),
    INDEX idx_output_id (output_id)
);
```

**citations テーブル**
```sql
CREATE TABLE citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_output_id VARCHAR(30) REFERENCES outputs(id),  -- 引用元
    target_output_id VARCHAR(30) REFERENCES outputs(id),  -- 引用先
    citation_type VARCHAR(20) NOT NULL,  -- agree/criticize/develop/reference
    excerpt TEXT,  -- 引用箇所抜粋
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_source (source_output_id),
    INDEX idx_target (target_output_id),
    UNIQUE(source_output_id, target_output_id, citation_type)
);
```

**agreements テーブル**
```sql
CREATE TABLE agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    output_id VARCHAR(30) REFERENCES outputs(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, output_id),
    INDEX idx_output_id (output_id),
    INDEX idx_created_at (created_at)
);
```

**hash_anchors テーブル**（Phase 3）
```sql
CREATE TABLE hash_anchors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    root_hash VARCHAR(64) NOT NULL,
    blockchain VARCHAR(20),  -- bitcoin/ethereum/opentimestamps
    transaction_id VARCHAR(255),
    anchored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_anchored_at (anchored_at)
);
```

**nft_tokens テーブル**（Phase 3）
```sql
CREATE TABLE nft_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    output_id VARCHAR(30) REFERENCES outputs(id),
    user_id UUID REFERENCES users(id),
    contract_address VARCHAR(42),  -- Ethereum address
    token_id BIGINT,
    blockchain VARCHAR(20),  -- polygon/ethereum
    ipfs_hash VARCHAR(100),  -- メタデータのIPFSハッシュ
    minted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_output_id (output_id),
    INDEX idx_user_id (user_id)
);
```

#### 2.3.2 Redis データ構造

**セッション管理**
```
Key: session:{user_id}
Type: String (JWT)
TTL: 7 days
```

**レート制限**
```
Key: ratelimit:{user_id}:{endpoint}
Type: String (カウンター)
TTL: 1 minute
```

**ランキングキャッシュ**
```
Key: ranking:daily
Type: Sorted Set (score: 引用数, member: output_id)
TTL: 1 hour
```

**新規性判定キャッシュ**（Phase 2）
```
Key: novelty:{output_hash}
Type: Hash (similar_ids, scores)
TTL: 24 hours
```

---

### 2.4 AI Review Service Layer

#### アーキテクチャ
```
┌──────────────┐
│   API        │ POST /api/v1/outputs
│   (FastAPI)  │
└──────┬───────┘
       │
       ↓ Celery Task Enqueue
┌──────────────┐
│   Redis      │ (Message Queue)
│   Broker     │
└──────┬───────┘
       │
       ↓ Task Consume
┌────────────────────────────────┐
│  AI Review Worker (Celery)     │
│  ┌──────────────────────────┐  │
│  │ 1. Content Moderation    │  │
│  │    (OpenAI Moderation)   │  │
│  │                          │  │
│  │ 2. Novelty Detection     │  │
│  │    (Embeddings + Cosine) │  │ Phase 2
│  │                          │  │
│  │ 3. Result Update         │  │
│  │    (PostgreSQL)          │  │
│  └──────────────────────────┘  │
└────────────────────────────────┘
       │
       ↓ WebSocket Notification
┌──────────────┐
│   Frontend   │ (Real-time Update)
└──────────────┘
```

#### フロー（Phase 1: コンテンツモデレーション）

1. **投稿作成**: ユーザーが投稿作成APIを叩く
2. **レコード作成**: `ai_review_status='pending'`でDBに保存
3. **タスクエンキュー**: Celeryタスク`review_content.delay(output_id)`
4. **非同期処理**:
   - OpenAI Moderation APIで暴力/性的/差別的コンテンツ検出
   - 問題あり → `ai_review_status='rejected'`
   - 問題なし → `ai_review_status='approved'`
5. **結果通知**: WebSocket経由でフロントエンドに通知

#### フロー（Phase 2: 新規性判定）

1. **埋め込み生成**: OpenAI Embeddings APIでベクトル化
2. **類似検索**: Pineconeで既存投稿との類似度計算
3. **スコアリング**: 最高類似度を元に新規性スコア算出
   - 新規性 = 100 - (最高類似度 * 100)
4. **振り分け**:
   - 新規性 >= 70% → `visibility='public'`
   - 新規性 < 70% → `visibility='private'`, 類似投稿を提示

---

### 2.5 Hash Chain Architecture

#### Merkle Tree構造

```
                    Root Hash (Daily)
                   /                \
            Branch Hash          Branch Hash
           /          \         /          \
      Output A    Output B  Output C    Output D
      (hash_A)    (hash_B)  (hash_C)    (hash_D)
```

#### ハッシュ計算ロジック

**投稿ハッシュ**
```python
def calculate_output_hash(output: Output) -> str:
    data = {
        "id": output.id,
        "user_id": str(output.user_id),
        "content": output.content,
        "version": output.version,
        "parent_hash": output.parent_hash or "",
        "created_at": output.created_at.isoformat()
    }
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()
```

**ルートハッシュ（日次）**
```python
def calculate_root_hash(daily_outputs: List[Output]) -> str:
    hashes = [output.hash for output in daily_outputs]
    hashes.sort()  # 順序固定
    combined = "".join(hashes)
    return hashlib.sha256(combined.encode()).hexdigest()
```

#### 改ざん検出フロー

1. **定期チェック**（週次バッチ）: 全投稿のハッシュ再計算
2. **不整合検出**: `calculated_hash != stored_hash`
3. **アラート**: Slack/メール通知 + ログ記録
4. **ロールバック**: 最新のバックアップから復元

---

### 2.6 Anchoring Service（Phase 3）

#### 日次アンカリングフロー

```
┌─────────────────┐
│  Cron Job       │ (毎日 AM 3:00 UTC)
│  (Cloud         │
│   Scheduler)    │
└────────┬────────┘
         │
         ↓ Trigger
┌─────────────────┐
│  Anchoring      │
│  Worker         │
│  (Celery)       │
└────────┬────────┘
         │
         ↓ 1. Calculate Root Hash
┌─────────────────┐
│  PostgreSQL     │ (前日の全投稿ハッシュ取得)
└────────┬────────┘
         │
         ↓ 2. Submit to OpenTimestamps
┌─────────────────┐
│ OpenTimestamps  │ (無料アンカリング)
│      API        │
└────────┬────────┘
         │
         ↓ 3. (Optional) Submit to Bitcoin
┌─────────────────┐
│   Bitcoin       │ (有料アンカリング)
│   Network       │
└────────┬────────┘
         │
         ↓ 4. Record Transaction ID
┌─────────────────┐
│  hash_anchors   │ (PostgreSQL)
│     Table       │
└─────────────────┘
```

#### コスト最適化

- **OpenTimestamps**: 無料、1日1回
- **Bitcoin**: 月1回のみ（月末締め）、コスト: 約1,000円/月
- **Ethereum**: 緊急時のみ（問題検出時）

---

### 2.7 NFT Minting Service（Phase 3）

#### NFTメタデータ構造（ERC-721）

```json
{
  "name": "Output Title",
  "description": "Excerpt of the output content...",
  "image": "ipfs://QmXXX.../thumbnail.png",
  "external_url": "https://sns.example.com/outputs/OUT-2026-0324-A1B2C3",
  "attributes": [
    {
      "trait_type": "Author",
      "value": "@username"
    },
    {
      "trait_type": "Category",
      "value": "Philosophy"
    },
    {
      "trait_type": "Citation Count",
      "value": 42
    },
    {
      "trait_type": "Novelty Score",
      "value": 95.5
    },
    {
      "trait_type": "Created At",
      "value": "2026-03-24"
    }
  ]
}
```

#### NFT発行フロー

```
┌──────────────┐
│   User       │ Click "Mint as NFT"
└──────┬───────┘
       │
       ↓ POST /api/v1/outputs/:id/nft
┌──────────────┐
│   Backend    │ 1. Check eligibility (Public, high score)
└──────┬───────┘
       │
       ↓ 2. Generate Metadata JSON
┌──────────────┐
│   IPFS       │ Upload metadata + thumbnail
└──────┬───────┘
       │ ipfs://QmXXX.../metadata.json
       │
       ↓ 3. Call Smart Contract
┌──────────────┐
│   Polygon    │ Mint ERC-721 Token
│   Network    │
└──────┬───────┘
       │ transaction_hash
       │
       ↓ 4. Record Token Info
┌──────────────┐
│ nft_tokens   │ (PostgreSQL)
│    Table     │
└──────────────┘
```

#### スマートコントラクト（Solidity）

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract OutputNFT is ERC721URIStorage, Ownable {
    uint256 private _tokenIds;

    constructor() ERC721("SNS Output NFT", "OUTPUT") {}

    function mintNFT(address recipient, string memory tokenURI)
        public
        onlyOwner
        returns (uint256)
    {
        _tokenIds++;
        uint256 newItemId = _tokenIds;
        _mint(recipient, newItemId);
        _setTokenURI(newItemId, tokenURI);
        return newItemId;
    }
}
```

---

## 3. セキュリティアーキテクチャ

### 3.1 認証フロー（JWT）

```
┌──────────────┐
│   Frontend   │
└──────┬───────┘
       │ 1. POST /auth/login (email, password)
       ↓
┌──────────────┐
│   Backend    │ 2. Validate credentials
└──────┬───────┘
       │
       ↓ 3. Generate Tokens
┌──────────────────────────────┐
│  Access Token (15 min TTL)   │
│  Refresh Token (7 days TTL)  │
└──────────────────────────────┘
       │
       ↓ 4. Return to Frontend
┌──────────────┐
│   Frontend   │ Store in Memory (Access) + HttpOnly Cookie (Refresh)
└──────┬───────┘
       │
       ↓ 5. Subsequent Requests (with Access Token)
┌──────────────┐
│   Backend    │ Verify JWT signature + expiration
└──────────────┘
       │
       ↓ 6. Access Token Expired
┌──────────────┐
│   Frontend   │ POST /auth/refresh (with Refresh Token)
└──────┬───────┘
       │
       ↓ 7. Issue New Access Token
┌──────────────┐
│   Backend    │
└──────────────┘
```

### 3.2 レート制限

- **ログイン試行**: 5回/5分（IPアドレス単位）
- **投稿作成**: 10回/時間（ユーザー単位）
- **引用作成**: 50回/時間
- **API全般**: 100リクエスト/分

### 3.3 データ暗号化

- **通信**: TLS 1.3
- **パスワード**: Argon2id
- **データベース**: At-rest encryption（Cloud SQL/RDS標準機能）
- **バックアップ**: 暗号化済みストレージ

---

## 4. 監視・運用アーキテクチャ

### 4.1 ログ収集

```
Application Logs → Cloud Logging/CloudWatch
  ├── Error Logs (Level: ERROR)
  ├── Access Logs (HTTP requests)
  ├── AI Review Logs (判定結果)
  └── Security Logs (認証試行)
```

### 4.2 メトリクス監視

- **API レスポンスタイム**: P50, P95, P99
- **エラー率**: 5xx errors / total requests
- **データベースパフォーマンス**: Query execution time
- **AI API使用量**: Tokens/day, Cost
- **ストレージ使用量**: GB

### 4.3 アラート設定

| 条件 | アラートレベル | 通知先 |
|------|--------------|--------|
| API エラー率 > 5% | Critical | Slack + Email |
| レスポンスタイム P95 > 3秒 | Warning | Slack |
| ハッシュ不整合検出 | Critical | Email + SMS |
| AI APIコスト > $100/day | Warning | Slack |
| ストレージ使用率 > 80% | Warning | Email |

---

## 5. スケーリング戦略

### 5.1 Phase 1（〜1,000ユーザー）

- **Backend**: 2インスタンス（Cloud Run）
- **Database**: 単一インスタンス（2 vCPU, 8GB RAM）
- **Redis**: 単一インスタンス（1GB）

### 5.2 Phase 2（1,000〜10,000ユーザー）

- **Backend**: Auto-scaling（2〜10インスタンス）
- **Database**: Read Replica追加（1台）
- **Redis**: クラスタ化

### 5.3 Phase 3（10,000〜100,000ユーザー）

- **Backend**: マイクロサービス分離
  - API Service
  - AI Review Service
  - Anchoring Service
- **Database**: 水平シャーディング（ユーザーID単位）
- **CDN**: 積極的なキャッシュ

---

## 6. 災害復旧（DR）

### 6.1 バックアップ戦略

- **PostgreSQL**:
  - Point-in-time recovery（1時間間隔）
  - 日次フルバックアップ（7日保存）
  - 週次バックアップ（4週保存）
  - 月次バックアップ（12ヶ月保存）

- **ストレージ（画像等）**:
  - Cross-region replication
  - Lifecycle policy（削除後90日はソフトデリート）

### 6.2 復旧手順

1. **障害検知**: モニタリングアラート
2. **影響範囲確認**: ログ分析
3. **フェイルオーバー**: Read Replica → Primary昇格
4. **データリストア**: 最新バックアップから復元
5. **整合性チェック**: ハッシュチェーン検証
6. **サービス再開**: 段階的にトラフィック戻す

**RTO**: 4時間、**RPO**: 1時間

---

## 7. 開発環境

### 7.1 ローカル開発環境（Docker Compose）

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: sns_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: uvicorn app.main:app --reload --host 0.0.0.0
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    command: npm run dev
    volumes:
      - ./frontend:/app
    ports:
      - "5173:5173"

  celery_worker:
    build: ./backend
    command: celery -A app.workers worker --loglevel=info
    depends_on:
      - redis
      - postgres
```

### 7.2 CI/CD パイプライン（GitHub Actions）

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Backend Tests
        run: |
          cd backend
          poetry install
          poetry run pytest
      - name: Run Frontend Tests
        run: |
          cd frontend
          pnpm install
          pnpm test

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: sns-backend
          region: us-central1
```

---

## 8. 次のステップ

1. **Week 1**: リポジトリ初期化、Docker Compose環境構築
2. **Week 2**: PostgreSQLマイグレーション作成、基本APIスケルトン
3. **Week 3**: 認証API実装、フロントエンド認証画面
4. **Week 4**: 投稿CRUD API実装、ハッシュチェーン統合

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 著者 |
|-----------|------|---------|------|
| 1.0 | 2026-03-24 | 初版作成 | - |
