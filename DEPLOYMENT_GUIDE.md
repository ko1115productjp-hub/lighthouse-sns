# Vercel + Supabase デプロイメントガイド

このガイドでは、Lighthouse of Intellect を **Vercel + Supabase + Upstash** 構成で本番環境にデプロイする手順を説明します。

## 🎯 構成の概要

- **フロントエンド**: Vercel (無料プラン可)
- **バックエンド**: Vercel Serverless Functions (無料プラン可)
- **データベース**: Supabase PostgreSQL with pgvector (500MB無料)
- **キャッシュ**: Upstash Redis (10,000リクエスト/日 無料)

**総コスト**: 無料プラン内で運用可能（API使用量次第）

---

## 📋 前提条件

- GitHubアカウント
- Vercelアカウント（GitHubで登録可）
- Supabaseアカウント（GitHubで登録可）
- Upstashアカウント（GitHubで登録可）
- 以下のAPIキー：
  - OpenAI API Key
  - Google OAuth Credentials
  - LINE OAuth Credentials
  - Serper API Key（任意）
  - Google Places API Key（任意）

---

## ステップ1: Supabase プロジェクトのセットアップ

### 1-1. プロジェクト作成

1. [Supabase Dashboard](https://app.supabase.com/) にアクセス
2. "New project" をクリック
3. 以下を入力：
   - **Name**: `lighthouse-prod`
   - **Database Password**: 強力なパスワードを生成（必ず保存）
   - **Region**: `Northeast Asia (Tokyo)` を選択
   - **Pricing Plan**: Free（500MB、無制限接続）
4. "Create new project" をクリック（2-3分待機）

### 1-2. pgvector 拡張機能の有効化

1. Supabase Dashboard で "Database" → "Extensions" を選択
2. 検索ボックスに `vector` と入力
3. **pgvector** を見つけて "Enable" をクリック

### 1-3. データベース接続情報の取得

1. "Project Settings" → "Database" を選択
2. 以下の情報をメモ：
   - **Host**: `db.xxx.supabase.co`
   - **Database name**: `postgres`
   - **Port**: `5432`
   - **User**: `postgres`
   - **Password**: プロジェクト作成時のパスワード

3. **Connection string（Pooler）**をコピー：
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:6543/postgres?pgbouncer=true
   ```

   ⚠️ **重要**: Vercel Serverless Functions では **Pooler接続（ポート6543）** を使用してください。
   - 通常接続（5432）: 最大60接続まで
   - Pooler接続（6543）: 無制限接続（推奨）

---

## ステップ2: Upstash Redis のセットアップ

### 2-1. データベース作成

1. [Upstash Console](https://console.upstash.com/) にアクセス
2. "Create Database" をクリック
3. 以下を入力：
   - **Name**: `lighthouse-redis`
   - **Type**: Regional
   - **Region**: `ap-northeast-1` (Tokyo)
   - **TLS**: Enabled（推奨）
4. "Create" をクリック

### 2-2. 接続情報の取得

1. 作成したデータベースをクリック
2. "Details" タブで以下をコピー：
   - **UPSTASH_REDIS_REST_URL**: `https://xxx.upstash.io`
   - **UPSTASH_REDIS_REST_TOKEN**: `Axxxxxx`

---

## ステップ3: Vercel バックエンドの準備

### 3-1. Vercel用のエントリーポイント作成

バックエンドをVercel Serverless Functionsとしてデプロイするため、専用のエントリーポイントを作成します。

```bash
# packages/backend/api/index.py を作成
```

このファイルは後で作成します。

### 3-2. requirements.txt の作成

Vercelはpoetryをサポートしていないため、requirements.txtを生成します。

```bash
cd packages/backend
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

### 3-3. vercel.json の作成（バックエンド）

バックエンドルートに `vercel.json` を作成します（後述）。

---

## ステップ4: データベースマイグレーション

### 4-1. ローカルから本番DBへマイグレーション

1. `.env.production` ファイルを作成：

```bash
# packages/backend/.env.production
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.xxx.supabase.co:6543/postgres?pgbouncer=true&ssl=require
```

2. マイグレーションを実行：

```bash
cd packages/backend
export $(cat .env.production | xargs)
poetry run alembic upgrade head
```

⚠️ **注意**: Pooler接続（6543）ではマイグレーションがエラーになる場合があります。その場合は一時的にDirect接続（5432）を使用してください。

---

## ステップ5: GitHub リポジトリのプッシュ

Vercelは Git連携でデプロイするため、コードをGitHubにプッシュします。

```bash
# リポジトリがまだない場合
git init
git add .
git commit -m "Initial commit for deployment"

# GitHubで新しいリポジトリを作成後
git remote add origin https://github.com/YOUR_USERNAME/lighthouse.git
git branch -M main
git push -u origin main
```

---

## ステップ6: Vercel フロントエンドのデプロイ

### 6-1. プロジェクトのインポート

1. [Vercel Dashboard](https://vercel.com/dashboard) にアクセス
2. "Add New" → "Project" をクリック
3. GitHubリポジトリを接続
4. `lighthouse` リポジトリを選択
5. 以下を設定：
   - **Framework Preset**: Vite
   - **Root Directory**: `packages/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### 6-2. 環境変数の設定

"Environment Variables" セクションで以下を追加：

| Name | Value |
|------|-------|
| `VITE_API_URL` | `https://lighthouse-backend.vercel.app` (後で更新) |

### 6-3. デプロイ

"Deploy" をクリックしてデプロイを開始。

デプロイ完了後、URLをメモ（例: `https://lighthouse-frontend.vercel.app`）

---

## ステップ7: Vercel バックエンドのデプロイ

### 7-1. 別プロジェクトとしてインポート

1. Vercel Dashboard で "Add New" → "Project"
2. 同じGitHubリポジトリを選択
3. 以下を設定：
   - **Project Name**: `lighthouse-backend`
   - **Framework Preset**: Other
   - **Root Directory**: `packages/backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Output Directory**: (空欄)

### 7-2. 環境変数の設定

以下の環境変数をすべて設定：

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.xxx.supabase.co:6543/postgres?pgbouncer=true&ssl=require

# Redis
REDIS_URL=https://xxx.upstash.io
REDIS_TOKEN=Axxxxxx

# Security
SECRET_KEY=（openssl rand -hex 32 で生成）
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["https://lighthouse-frontend.vercel.app"]

# OpenAI
OPENAI_API_KEY=sk-proj-...

# Serper (Optional)
SERPER_API_KEY=...

# Google APIs
GOOGLE_PLACES_API_KEY=...
GOOGLE_BOOKS_API_KEY=...

# OAuth - Google
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://lighthouse-backend.vercel.app/api/v1/auth/google/callback

# OAuth - LINE
LINE_CHANNEL_ID=...
LINE_CHANNEL_SECRET=...
LINE_REDIRECT_URI=https://lighthouse-backend.vercel.app/api/v1/auth/line/callback

# Originality Settings
ORIGINALITY_THRESHOLD=60
SIMILARITY_THRESHOLD=0.85
```

### 7-3. デプロイ

"Deploy" をクリック。

デプロイ完了後、URLをメモ（例: `https://lighthouse-backend.vercel.app`）

---

## ステップ8: CORS と OAuth のURL更新

### 8-1. フロントエンドの環境変数更新

1. フロントエンドプロジェクトの "Settings" → "Environment Variables"
2. `VITE_API_URL` を実際のバックエンドURLに更新：
   ```
   VITE_API_URL=https://lighthouse-backend.vercel.app
   ```
3. "Redeploy" でフロントエンドを再デプロイ

### 8-2. Google OAuth設定の更新

1. [Google Cloud Console](https://console.cloud.google.com/)
2. "APIs & Services" → "Credentials"
3. OAuth 2.0 Client IDを選択
4. "Authorized redirect URIs" に追加：
   ```
   https://lighthouse-backend.vercel.app/api/v1/auth/google/callback
   https://lighthouse-frontend.vercel.app/oauth-callback
   ```

### 8-3. LINE OAuth設定の更新

1. [LINE Developers Console](https://developers.line.biz/)
2. チャネルを選択
3. "Callback URL" に追加：
   ```
   https://lighthouse-backend.vercel.app/api/v1/auth/line/callback
   ```

---

## ステップ9: 動作確認

### 9-1. ヘルスチェック

ブラウザで以下にアクセス：
```
https://lighthouse-backend.vercel.app/api/v1/health
```

期待される結果：
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### 9-2. フロントエンドアクセス

```
https://lighthouse-frontend.vercel.app
```

ログイン画面が表示されることを確認。

### 9-3. OAuth動作確認

1. "Googleでログイン" をクリック
2. Google認証を完了
3. タイムラインにリダイレクトされることを確認

---

## トラブルシューティング

### ❌ Database connection failed

**原因**: Pooler接続でSSLが無効
**解決策**: DATABASE_URLに `?ssl=require` を追加

### ❌ Too many database connections

**原因**: Direct接続（5432）を使用している
**解決策**: Pooler接続（6543）に変更

### ❌ CORS error

**原因**: `CORS_ORIGINS` が正しく設定されていない
**解決策**: バックエンドの環境変数で実際のフロントエンドURLを配列形式で設定

### ❌ Module not found error

**原因**: requirements.txt が古い
**解決策**:
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
git commit -am "Update requirements.txt"
git push
```

---

## 📊 コスト見積もり

### 無料枠内の場合

- Vercel: $0（100GB帯域、Serverless Function 100GBh）
- Supabase: $0（500MB DB、無制限API）
- Upstash: $0（10,000リクエスト/日）
- **合計**: $0/月

### 有料プランが必要になるケース

- Vercel Pro ($20/月): 帯域1TB超過、商用利用
- Supabase Pro ($25/月): 8GB DB、優先サポート
- Upstash Pay-as-you-go: 10,000リクエスト/日超過時

---

## 🎉 次のステップ

1. カスタムドメインの設定（Vercel Settings → Domains）
2. アナリティクスの有効化（Vercel Analytics）
3. 本番用のログ監視設定（Sentry等）
4. 定期バックアップの設定（Supabase Dashboard）

これでデプロイ完了です！
