# 開発環境セットアップガイド

## 目次
1. [前提条件](#前提条件)
2. [初回セットアップ](#初回セットアップ)
3. [開発サーバーの起動](#開発サーバーの起動)
4. [よく使うコマンド](#よく使うコマンド)
5. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

### 必須（Docker使用の場合）
- **Docker Desktop** 4.0+ ([ダウンロード](https://www.docker.com/products/docker-desktop))
- **Git** 2.0+

### 必須（ローカル開発の場合）
- **Node.js** 18+ ([ダウンロード](https://nodejs.org/))
- **pnpm** 8+ (インストール: `npm install -g pnpm`)
- **Python** 3.12+ ([ダウンロード](https://www.python.org/downloads/))
- **Poetry** 1.7+ (インストール: `pip install poetry`)
- **PostgreSQL** 16+ ([ダウンロード](https://www.postgresql.org/download/))
- **Redis** 7+ ([ダウンロード](https://redis.io/download))

---

## 初回セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-org/sns-draft.git
cd sns-draft
```

### 2. 環境変数の設定

```bash
# バックエンドの環境変数
cp packages/backend/.env.example packages/backend/.env

# .envファイルを編集（必要に応じて）
# - SECRET_KEY: openssl rand -hex 32 で生成
# - OPENAI_API_KEY: OpenAIのAPIキー（Phase 1では任意）
```

### 3. セットアップ方法の選択

#### 方法A: Docker Compose（推奨）

```bash
# すべてのサービスを起動
docker-compose up -d

# ログ確認
docker-compose logs -f

# 初回のみ: バックエンドの依存関係インストール
docker-compose exec backend poetry install

# 初回のみ: フロントエンドの依存関係インストール
docker-compose exec frontend pnpm install
```

アクセス:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

#### 方法B: ローカル開発

**Step 1: データベースとRedisを起動（Docker）**
```bash
docker-compose up -d postgres redis
```

**Step 2: バックエンドのセットアップ**
```bash
cd packages/backend

# Poetry で依存関係をインストール
poetry install

# データベースマイグレーション（今後実装）
# poetry run alembic upgrade head

# 開発サーバー起動
poetry run uvicorn app.main:app --reload
```

Backend API: http://localhost:8000

**Step 3: フロントエンドのセットアップ**
```bash
cd packages/frontend

# 依存関係インストール
pnpm install

# 開発サーバー起動
pnpm run dev
```

Frontend: http://localhost:5173

---

## 開発サーバーの起動

### Docker Composeを使用

```bash
# すべてのサービスを起動
docker-compose up -d

# 特定のサービスのみ起動
docker-compose up -d postgres redis backend

# ログをリアルタイムで確認
docker-compose logs -f backend

# すべて停止
docker-compose down

# データも削除して停止（注意: データベースの内容も削除されます）
docker-compose down -v
```

### ローカル開発

**ターミナル1: バックエンド**
```bash
cd packages/backend
poetry run uvicorn app.main:app --reload
```

**ターミナル2: フロントエンド**
```bash
cd packages/frontend
pnpm run dev
```

---

## よく使うコマンド

### Monorepo全体

```bash
# すべてのパッケージのLint実行
pnpm run lint

# すべてのパッケージのフォーマット
pnpm run format

# すべてのパッケージのビルド
pnpm run build

# すべてのパッケージのテスト実行
pnpm run test
```

### バックエンド

```bash
cd packages/backend

# 依存関係の追加
poetry add package-name

# 開発用依存関係の追加
poetry add --group dev package-name

# コードフォーマット
poetry run black .

# Lint実行
poetry run ruff check .

# 型チェック
poetry run mypy app

# テスト実行
poetry run pytest

# カバレッジ付きテスト
poetry run pytest --cov=app --cov-report=html

# データベースマイグレーション作成
poetry run alembic revision --autogenerate -m "description"

# マイグレーション適用
poetry run alembic upgrade head

# ロールバック
poetry run alembic downgrade -1
```

### フロントエンド

```bash
cd packages/frontend

# 依存関係の追加
pnpm add package-name

# 開発用依存関係の追加
pnpm add -D package-name

# Lint実行
pnpm run lint

# テスト実行
pnpm run test

# ビルド
pnpm run build

# ビルド結果のプレビュー
pnpm run preview
```

### Docker

```bash
# コンテナ一覧
docker-compose ps

# コンテナ内でコマンド実行
docker-compose exec backend bash
docker-compose exec frontend sh

# ログ確認
docker-compose logs -f backend
docker-compose logs -f frontend

# コンテナ再ビルド
docker-compose build backend
docker-compose build frontend

# すべて再ビルドして起動
docker-compose up -d --build

# 特定のサービスのみ再起動
docker-compose restart backend
```

---

## トラブルシューティング

### ポートが既に使用されている

**エラー**: `Port 5432 is already in use`

**解決策**:
```bash
# Windowsの場合
netstat -ano | findstr :5432
taskkill /PID <PID> /F

# Linux/Macの場合
lsof -ti:5432 | xargs kill -9
```

または、docker-compose.ymlのポート番号を変更:
```yaml
ports:
  - '5433:5432'  # 5432 → 5433に変更
```

### Docker Composeが起動しない

**解決策**:
```bash
# すべてのコンテナとボリュームを削除
docker-compose down -v

# Dockerイメージのキャッシュをクリア
docker system prune -a

# 再ビルドして起動
docker-compose up -d --build
```

### バックエンドのPoetry依存関係エラー

**解決策**:
```bash
cd packages/backend

# Poetryのキャッシュをクリア
poetry cache clear pypi --all

# 依存関係を再インストール
poetry install --no-cache
```

### フロントエンドのnode_modules エラー

**解決策**:
```bash
cd packages/frontend

# node_modules削除
rm -rf node_modules

# pnpmのキャッシュクリア（Windows）
pnpm store prune

# 再インストール
pnpm install
```

### データベース接続エラー

**エラー**: `could not connect to server: Connection refused`

**解決策**:
1. PostgreSQLが起動しているか確認:
   ```bash
   docker-compose ps postgres
   ```

2. 環境変数の確認:
   ```bash
   # packages/backend/.env
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sns_dev
   ```

3. Dockerの場合、ホスト名を変更:
   ```bash
   # localhost → postgres
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/sns_dev
   ```

### API が 404 を返す

**原因**: Viteのプロキシ設定が正しくない

**解決策**:
```typescript
// packages/frontend/vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

### CORS エラー

**原因**: バックエンドのCORS設定が不足

**解決策**:
```bash
# packages/backend/.env
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

---

## 開発フロー

### 1. 新機能開発

```bash
# 1. 新しいブランチを作成
git checkout -b feature/new-feature

# 2. 開発環境を起動
docker-compose up -d

# 3. コードを編集（ホットリロードで自動反映）

# 4. テストを実行
cd packages/backend
poetry run pytest

cd packages/frontend
pnpm run test

# 5. Lint とフォーマット
pnpm run lint
pnpm run format

# 6. コミット
git add .
git commit -m "feat: add new feature"

# 7. プッシュ
git push origin feature/new-feature
```

### 2. データベーススキーマ変更

```bash
# 1. モデルを編集（packages/backend/app/models/*.py）

# 2. マイグレーションファイル生成
cd packages/backend
poetry run alembic revision --autogenerate -m "add new table"

# 3. マイグレーション確認
# alembic/versions/xxxx_add_new_table.py を確認

# 4. マイグレーション適用
poetry run alembic upgrade head

# 5. テスト
poetry run pytest
```

---

## 次のステップ

開発環境が正しくセットアップできたら:

1. [docs/design/api-design.md](design/api-design.md) でAPI仕様を確認
2. [docs/tasks/task-breakdown.md](tasks/task-breakdown.md) で実装タスクを確認
3. 最初のタスク: 認証APIの実装

---

## 参考リンク

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
