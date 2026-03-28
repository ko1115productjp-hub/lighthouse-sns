# 🚀 Lighthouse デプロイメントチェックリスト

このチェックリストに従って、Vercel + Supabase + Upstash へのデプロイを完了させましょう。

---

## ✅ 事前準備

- [ ] GitHubアカウント作成
- [ ] Vercelアカウント作成（GitHubでサインアップ）
- [ ] Supabaseアカウント作成（GitHubでサインアップ）
- [ ] Upstashアカウント作成（GitHubでサインアップ）

---

## 📦 ステップ1: Supabase データベース

### 1-1. プロジェクト作成
- [ ] [Supabase Dashboard](https://app.supabase.com/) を開く
- [ ] "New project" をクリック
- [ ] プロジェクト名: `lighthouse-prod`
- [ ] データベースパスワードを生成して**安全に保存**
- [ ] リージョン: `Northeast Asia (Tokyo)`
- [ ] "Create new project" をクリック（2-3分待機）

### 1-2. pgvector 有効化
- [ ] "Database" → "Extensions" を選択
- [ ] `vector` を検索
- [ ] **pgvector** を "Enable"

### 1-3. 接続情報を取得
- [ ] "Project Settings" → "Database" を選択
- [ ] **Connection string (Pooler)** をコピー
  ```
  postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:6543/postgres?pgbouncer=true
  ```
- [ ] メモ帳に保存しておく

---

## 🔴 ステップ2: Upstash Redis

### 2-1. データベース作成
- [ ] [Upstash Console](https://console.upstash.com/) を開く
- [ ] "Create Database" をクリック
- [ ] データベース名: `lighthouse-redis`
- [ ] Type: Regional
- [ ] Region: `ap-northeast-1` (Tokyo)
- [ ] TLS: Enabled
- [ ] "Create" をクリック

### 2-2. 接続情報を取得
- [ ] 作成したデータベースをクリック
- [ ] "Details" タブを開く
- [ ] **UPSTASH_REDIS_REST_URL** をコピー
- [ ] **UPSTASH_REDIS_REST_TOKEN** をコピー
- [ ] メモ帳に保存しておく

---

## 🗄️ ステップ3: データベースマイグレーション

### 3-1. ローカルで .env.production を作成

```bash
cd packages/backend
cp .env.production.example .env.production
```

### 3-2. .env.production を編集

以下の値を Supabase の接続情報に置き換える：

```env
DATABASE_URL=postgresql+asyncpg://postgres:[YOUR_PASSWORD]@db.xxx.supabase.co:5432/postgres?ssl=require
```

⚠️ **注意**: マイグレーション時は **Direct接続（ポート5432）** を使用

### 3-3. マイグレーション実行

Windowsの場合（PowerShell）:
```powershell
cd packages/backend
$env:DATABASE_URL = "postgresql+asyncpg://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres?ssl=require"
poetry run alembic upgrade head
```

macOS/Linuxの場合:
```bash
cd packages/backend
export DATABASE_URL="postgresql+asyncpg://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres?ssl=require"
poetry run alembic upgrade head
```

Dockerを使用する場合:
```bash
docker exec sns-backend sh -c "export DATABASE_URL='postgresql+asyncpg://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres?ssl=require' && alembic upgrade head"
```

- [ ] マイグレーションが成功したことを確認

---

## 📤 ステップ4: GitHub へプッシュ

### 4-1. リポジトリ作成（まだの場合）

```bash
git init
git add .
git commit -m "feat: Initial commit for deployment"
```

### 4-2. GitHub でリポジトリ作成
- [ ] [GitHub](https://github.com/new) で新しいリポジトリを作成
- [ ] リポジトリ名: `lighthouse` （任意）
- [ ] Private/Public を選択
- [ ] "Create repository" をクリック

### 4-3. リモートを追加してプッシュ

```bash
git remote add origin https://github.com/YOUR_USERNAME/lighthouse.git
git branch -M main
git push -u origin main
```

- [ ] GitHubにコードがプッシュされたことを確認

---

## 🌐 ステップ5: Vercel バックエンドのデプロイ

### 5-1. プロジェクトをインポート
- [ ] [Vercel Dashboard](https://vercel.com/dashboard) を開く
- [ ] "Add New" → "Project" をクリック
- [ ] GitHubリポジトリを接続
- [ ] `lighthouse` リポジトリを選択

### 5-2. ビルド設定
- [ ] **Project Name**: `lighthouse-backend`
- [ ] **Framework Preset**: Other
- [ ] **Root Directory**: `packages/backend` を選択
- [ ] **Build Command**: `pip install -r requirements.txt`
- [ ] **Output Directory**: (空欄のまま)

### 5-3. 環境変数を設定

"Environment Variables" セクションで以下をすべて追加：

必須の環境変数:
```
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.xxx.supabase.co:6543/postgres?pgbouncer=true&ssl=require
REDIS_URL=https://xxx.upstash.io
REDIS_TOKEN=Axxxxxx
SECRET_KEY=（openssl rand -hex 32 で生成）
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["https://lighthouse-frontend.vercel.app"]
OPENAI_API_KEY=sk-proj-xxxxx
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxx
GOOGLE_REDIRECT_URI=https://lighthouse-backend.vercel.app/api/v1/auth/google/callback
LINE_CHANNEL_ID=xxxxx
LINE_CHANNEL_SECRET=xxxxx
LINE_REDIRECT_URI=https://lighthouse-backend.vercel.app/api/v1/auth/line/callback
ORIGINALITY_THRESHOLD=60
SIMILARITY_THRESHOLD=0.85
DEBUG=False
```

オプション（後で追加可）:
```
SERPER_API_KEY=xxxxx
GOOGLE_PLACES_API_KEY=xxxxx
GOOGLE_BOOKS_API_KEY=xxxxx
```

- [ ] すべての環境変数を設定完了

### 5-4. デプロイ
- [ ] "Deploy" をクリック
- [ ] デプロイ完了まで待機（3-5分）
- [ ] デプロイURLをコピー（例: `https://lighthouse-backend.vercel.app`）

---

## 🎨 ステップ6: Vercel フロントエンドのデプロイ

### 6-1. 新しいプロジェクトをインポート
- [ ] Vercel Dashboard で "Add New" → "Project"
- [ ] 同じGitHubリポジトリを選択

### 6-2. ビルド設定
- [ ] **Project Name**: `lighthouse-frontend`
- [ ] **Framework Preset**: Vite
- [ ] **Root Directory**: `packages/frontend` を選択
- [ ] **Build Command**: `npm run build`
- [ ] **Output Directory**: `dist`

### 6-3. 環境変数を設定

```
VITE_API_URL=https://lighthouse-backend.vercel.app
```

⚠️ **重要**: 実際のバックエンドURLに置き換えてください

- [ ] 環境変数を設定完了

### 6-4. デプロイ
- [ ] "Deploy" をクリック
- [ ] デプロイ完了まで待機（2-3分）
- [ ] デプロイURLをコピー（例: `https://lighthouse-frontend.vercel.app`）

---

## 🔄 ステップ7: OAuth設定の更新

### 7-1. Google OAuth設定
- [ ] [Google Cloud Console](https://console.cloud.google.com/) を開く
- [ ] "APIs & Services" → "Credentials" を選択
- [ ] OAuth 2.0 Client ID を選択
- [ ] "Authorized redirect URIs" に以下を追加:
  ```
  https://lighthouse-backend.vercel.app/api/v1/auth/google/callback
  https://lighthouse-frontend.vercel.app/oauth-callback
  ```
- [ ] "Save" をクリック

### 7-2. LINE OAuth設定
- [ ] [LINE Developers Console](https://developers.line.biz/) を開く
- [ ] チャネルを選択
- [ ] "Callback URL" に追加:
  ```
  https://lighthouse-backend.vercel.app/api/v1/auth/line/callback
  ```
- [ ] "Update" をクリック

### 7-3. バックエンド環境変数を更新
- [ ] Vercel Dashboard → `lighthouse-backend` プロジェクト
- [ ] "Settings" → "Environment Variables"
- [ ] `CORS_ORIGINS` を実際のフロントエンドURLに更新:
  ```
  ["https://lighthouse-frontend.vercel.app"]
  ```
- [ ] "Redeploy" で再デプロイ

---

## ✅ ステップ8: 動作確認

### 8-1. ヘルスチェック
- [ ] ブラウザで以下にアクセス:
  ```
  https://lighthouse-backend.vercel.app/api/v1/health
  ```
- [ ] 以下のレスポンスが返ることを確認:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "redis": "connected"
  }
  ```

### 8-2. フロントエンドアクセス
- [ ] ブラウザで以下にアクセス:
  ```
  https://lighthouse-frontend.vercel.app
  ```
- [ ] ログイン画面が表示されることを確認

### 8-3. ログイン機能の確認
- [ ] "Googleでログイン" をクリック
- [ ] Google認証を完了
- [ ] タイムラインにリダイレクトされることを確認

### 8-4. 投稿機能の確認
- [ ] "投稿する" ボタンをクリック
- [ ] テスト投稿を作成
- [ ] AI査読が実行されることを確認
- [ ] タイムラインに投稿が表示されることを確認

---

## 🎉 完了！

すべてのチェックが完了したら、デプロイ成功です！

### 次にやること

- [ ] カスタムドメインの設定（Vercel Settings → Domains）
- [ ] アナリティクスの有効化（Vercel Analytics）
- [ ] エラー監視の設定（Sentry等）
- [ ] Supabaseの自動バックアップ確認

---

## 🔧 トラブルシューティング

問題が発生した場合は [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) の「トラブルシューティング」セクションを参照してください。

### よくある問題

1. **Database connection failed**
   - DATABASE_URLに `?ssl=require` が含まれているか確認
   - Pooler接続（6543）を使用しているか確認

2. **CORS error**
   - `CORS_ORIGINS` が正しく設定されているか確認
   - JSON配列形式になっているか確認: `["https://..."]`

3. **Module not found**
   - requirements.txt が最新か確認
   - 再度 `poetry export` を実行して git push

4. **OAuth redirect error**
   - Google/LINE の Callback URL が正しく設定されているか確認
   - バックエンドURLが正しいか確認
