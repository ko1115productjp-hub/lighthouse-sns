# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 出力の形式
回答は全て日本語で行ってください。

## Project Overview

**「Lighthouse of Intellect（知の灯台）」** - 人類の知の地層を形成するパブリック・アーカイブ

従来のSNSが瞬間的な感情刺激に偏る課題を解決し、「誰が言ったか」という権威性を徹底的に排除。
内容の**独自性・新規性・一次性**のみを、LLMとコミュニティによる査読を通じて評価し、永続化する。

### 基本原則
1. **客観的評価の至上主義** - 投稿者の実績やフォロワー数ではなく、内容の論理整合性と希少性のみを評価
2. **無自覚な貢献の称揚** - ユーザーが価値を自覚していなくとも、システムが客観的に知の財産と判断したものを昇格
3. **改ざん不可能な履歴** - すべての投稿・修正・批判を永久保存。退会後も知の系譜から消えない
4. **18歳以上の聖域** - 責任ある言論と論理整合性を担保

## Core Concepts

### 不可逆性の設計
- **採用方式**: ハッシュチェーン + 外部アンカリング（ブロックチェーン不使用）
- **内部**: PostgreSQL + Merkle Tree構造、SHA-256ハッシュ
- **外部**: 1日1回、Bitcoin/EthereumまたはOpenTimestampsにルートハッシュを記録
- 全ての変更履歴は永続的に記録され、改ざん・削除不可

### コンテンツ分類
- **Public Output**: AI査読を通過し新規性が認められた投稿（全ユーザーに公開）
- **Private Output**: 新規性なしと判定された投稿（フォロワー限定）

### 引用システム
- 全投稿に一意のシステム生成IDを付与
- 学術論文形式での引用・被引用関係を追跡
- 引用数と支持に基づくサジェストアルゴリズム（PageRankライク）

## Key Documents

### Core Philosophy
- `docs/the_lighthouse_protocol.md` - **プロトコル定義書**：プラットフォームの核心思想と基本原則

### Requirements & Design
- `docs/concept/SNS-concept-analysis.md` - コンセプト分析、課題、50のアイディア、技術設計方針
- `docs/requirements/requirements.md` - 機能要件・非機能要件・データモデル
- `docs/requirements/lighthouse-protocol-requirements.md` - **Lighthouse Protocol実装要件**
- `docs/design/tech-stack.md` - 技術スタック選定
- `docs/design/architecture.md` - システムアーキテクチャ
- `docs/design/api-design.md` - API設計
- `docs/tasks/task-breakdown.md` - フェーズ別タスク分解

### Progress Tracking
- `docs/IMPLEMENTATION_STATUS.md` - **実装状況サマリー**：完了機能・残タスク・優先度マッピング

## Development Commands

### Start Development Environment
```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Backend (FastAPI)
```bash
cd packages/backend

# Install dependencies
poetry install

# Run development server
poetry run uvicorn app.main:app --reload

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run ruff check .
```

### Frontend (React + Vite)
```bash
cd packages/frontend

# Install dependencies
pnpm install

# Run development server
pnpm run dev

# Build for production
pnpm run build

# Run tests
pnpm run test
```

### Database Migrations
```bash
cd packages/backend

# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + SQLAlchemy
- **Frontend**: TypeScript + React 18 + Vite + Tailwind CSS
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Monorepo**: Turborepo + pnpm workspaces
