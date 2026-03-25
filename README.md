# SNS Draft - 作品性を持つSNSプラットフォーム

長期的な思考と作品性を促進するSNSプラットフォームの企画・開発リポジトリ

## コンセプト

従来のSNSが抱える「瞬間的で忘れ去られるコンテンツ」の課題を解決し、学術論文のような引用システムと永続的な履歴管理を特徴とするプラットフォーム。

## 主要機能

- **不可逆性**: ハッシュチェーン + 外部アンカリングによる改ざん防止
- **学術的引用システム**: 投稿間の引用関係を追跡・可視化
- **AI査読**: コンテンツモデレーションと新規性判定
- **Public/Private Output**: 新規性に基づくコンテンツ分類
- **Kindle出版連携**: 高評価なPublic Outputを電子書籍化

## フォルダ構造

```
sns-draft/
├── docs/                  # ドキュメント
│   ├── concept/           # コンセプト文書
│   ├── requirements/      # 要件定義
│   ├── design/            # 設計書
│   └── tasks/             # タスク分解
├── packages/              # モノレポ構成
│   ├── backend/           # FastAPI バックエンド
│   │   ├── app/           # アプリケーションコード
│   │   │   ├── models/    # SQLAlchemy モデル
│   │   │   ├── routers/   # API エンドポイント
│   │   │   ├── schemas/   # Pydantic スキーマ
│   │   │   └── utils/     # ユーティリティ
│   │   └── tests/         # テスト (88テスト)
│   └── frontend/          # React フロントエンド
│       ├── src/
│       │   ├── components/ # UIコンポーネント
│       │   ├── pages/      # ページコンポーネント
│       │   ├── store/      # Zustand状態管理
│       │   └── lib/        # APIクライアント
│       └── public/
├── docker-compose.yml     # Docker設定
├── CLAUDE.md              # Claude Code向けガイド
└── README.md              # このファイル
```

## ドキュメント

### コンセプト
- [SNS-concept-analysis.md](docs/concept/SNS-concept-analysis.md) - 類似サービス分析、課題、50のアイディア

### 要件定義
- [requirements.md](docs/requirements/requirements.md) - 機能要件・非機能要件・データモデル

### 設計
- [architecture.md](docs/design/architecture.md) - システムアーキテクチャ
- [tech-stack.md](docs/design/tech-stack.md) - 技術スタック選定
- [api-design.md](docs/design/api-design.md) - API設計

### タスク管理
- [task-breakdown.md](docs/tasks/task-breakdown.md) - フェーズ別タスク分解

## 開発環境セットアップ

### 前提条件

- Docker & Docker Compose
- Node.js 18+ (ローカル開発の場合)
- Python 3.12+ (ローカル開発の場合)
- pnpm 8+ (ローカル開発の場合)

### クイックスタート（Docker使用）

```bash
# リポジトリのクローン
git clone https://github.com/your-org/sns-draft.git
cd sns-draft

# 環境変数の設定
cp packages/backend/.env.example packages/backend/.env

# Docker Composeで全サービスを起動
docker-compose up -d

# ログ確認
docker-compose logs -f
```

アクセス:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### ローカル開発（Docker不使用）

#### バックエンド

```bash
cd packages/backend

# Poetry で依存関係をインストール
poetry install

# 環境変数設定
cp .env.example .env

# PostgreSQL と Redis を起動（Docker）
docker-compose up -d postgres redis

# 開発サーバー起動
poetry run uvicorn app.main:app --reload
```

#### フロントエンド

```bash
cd packages/frontend

# 依存関係インストール
pnpm install

# 開発サーバー起動
pnpm run dev
```

### よく使うコマンド

```bash
# すべてのサービスを起動
docker-compose up -d

# 特定のサービスのみ起動
docker-compose up -d postgres redis

# ログ確認
docker-compose logs -f backend

# すべて停止
docker-compose down

# データも削除して停止
docker-compose down -v

# Lintとフォーマット
pnpm run lint
pnpm run format
```

### データベースマイグレーション

```bash
cd packages/backend

# マイグレーション作成
poetry run alembic revision --autogenerate -m "description"

# マイグレーション適用
poetry run alembic upgrade head

# ロールバック
poetry run alembic downgrade -1
```

## 実装状況

### ✅ 完了済み (Phase 1)

#### バックエンド API (FastAPI + PostgreSQL)
- ✅ **認証システム** - JWT認証、ユーザー登録・ログイン、Google/LINE OAuth (15テスト)
- ✅ **ユーザー管理** - プロフィール、検索、フォロー機能 (18テスト)
- ✅ **投稿管理 (Output)** - 作成、編集、履歴、タイムライン (18テスト)
- ✅ **引用システム (Citation)** - 4種類の引用タイプ、引用グラフ (13テスト)
- ✅ **同意システム (Agreement)** - 投稿への同意・取消 (14テスト)
- ✅ **ハッシュチェーン** - SHA-256によるバージョン管理
- ✅ **AIモデレーション** - OpenAI APIによるコンテンツチェック
- ✅ **新規性判定** - スコアに基づくPublic/Private振り分け

**テストカバレッジ**: 88/88テスト合格 ✅

#### フロントエンド (React + TypeScript)
- ✅ **基本構造** - React Router、Zustand状態管理、Tailwind CSS
- ✅ **APIクライアント** - Axios、認証インターセプター
- ✅ **認証画面** - ログイン、ユーザー登録
- ✅ **タイムライン** - Public/Private投稿フィルタリング
- ✅ **レイアウト** - ヘッダー、ナビゲーション、フッター
- ✅ **投稿作成画面** - Markdown対応、カテゴリ選択、タグ入力、プレビュー機能
- ✅ **投稿編集画面** - バージョン履歴表示、変更検出
- ✅ **投稿詳細画面** - 詳細表示、引用・同意機能、ハッシュチェーン表示
- ✅ **ユーザープロフィール画面** - 投稿一覧、同意した投稿、フォロワー/フォロー中、フォロー機能
- ✅ **プロフィール編集画面** - 表示名・自己紹介の編集

### 🚧 開発中

#### フロントエンド
- ⏳ 引用作成機能の統合
- ⏳ 引用グラフ可視化

### 📋 今後の計画

#### Phase 2: 差別化機能
- 高度な新規性判定AI
- 引用グラフの可視化強化
- レコメンデーションアルゴリズム

#### Phase 3: エコシステム
- 外部アンカリング（Bitcoin/Ethereum/OpenTimestamps）
- Kindle出版連携
- DAO移行

## ライセンス

TBD
