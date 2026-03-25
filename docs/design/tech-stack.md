# 技術スタック選定書

**作成日**: 2026-03-24
**バージョン**: 1.0

---

## 1. 技術選定方針

### 1.1 選定基準
1. **開発生産性**: 短期間でMVPを構築可能
2. **スケーラビリティ**: 100万ユーザーまで対応可能
3. **エコシステム**: ライブラリ・ツールが充実
4. **長期保守性**: コミュニティが活発で長期サポートが期待できる
5. **コスト効率**: インフラコストを抑制

### 1.2 アーキテクチャパターン
- **Monorepo**: バックエンド・フロントエンドを1リポジトリで管理
- **マイクロサービス（Phase 3）**: AI査読、アンカリング等は独立サービス化
- **イベント駆動**: 非同期処理にメッセージキュー使用

---

## 2. バックエンド

### 2.1 言語・フレームワーク

#### 選定: **Python + FastAPI**

**理由**:
- AI/ML統合が容易（OpenAI SDK、Hugging Face等）
- 非同期処理対応（async/await）
- 開発速度が速い（自動型検証、OpenAPI自動生成）
- データサイエンス系ライブラリが豊富

**代替案**:
- Node.js + Express/Nest.js: フロントエンドと言語統一できるが、AI統合がやや弱い
- Go: パフォーマンス優秀だが、AI/MLエコシステムが弱い

**バージョン**: Python 3.12+, FastAPI 0.110+

### 2.2 データベース

#### メインDB: **PostgreSQL 16**

**理由**:
- JSONB型でスキーマレス対応
- Full-text Search対応
- ACID特性で整合性保証
- pgvectorで埋め込みベクトル保存可能（Phase 2）

**用途**:
- User, Output, Citation, Agreement等のメインデータ

#### ベクトルDB: **Pinecone / Weaviate**（Phase 2）

**理由**:
- 新規性判定の類似度検索
- スケーラブルで低レイテンシ

**選定**: Pinecone（マネージドで運用楽）、コスト次第でWeaviate（セルフホスト）

#### キャッシュ: **Redis 7**

**用途**:
- セッション管理
- API レート制限
- ホットデータキャッシュ（ランキング等）

### 2.3 認証

**選定**: **Auth0 / Supabase Auth**

**理由**:
- ソーシャルログイン統合済み
- JWT発行・検証
- セキュリティベストプラクティス対応

**代替案**: 自前実装（PassportJS/Authlib） - Phase 1は既製品、Phase 3でカスタマイズ検討

### 2.4 ストレージ

#### オブジェクトストレージ: **AWS S3 / Google Cloud Storage**

**用途**:
- 画像・添付ファイル
- 生成されたEPUBファイル

**選定基準**: AWS利用ならS3、GCP利用ならGCS

#### 分散ストレージ: **IPFS + Filecoin**（Phase 3）

**用途**:
- 長期保存が必要な画像・メディア
- 投稿コンテンツのバックアップ

### 2.5 非同期処理・メッセージキュー

**選定**: **Celery + Redis / AWS SQS**

**用途**:
- AI査読の非同期処理
- 新規性判定
- 外部アンカリングバッチ
- メール送信

**理由**: Celeryは Python エコシステムで標準的

---

## 3. フロントエンド

### 3.1 言語・フレームワーク

**選定**: **TypeScript + React + Vite**

**理由**:
- 型安全性（TypeScript）
- コンポーネントエコシステムが豊富
- Viteで高速開発環境
- SSR不要（SEOは後で対応）

**バージョン**: TypeScript 5.x, React 18.x, Vite 5.x

### 3.2 UIライブラリ

**選定**: **Tailwind CSS + shadcn/ui**

**理由**:
- 迅速なUI構築
- shadcn/uiでアクセシビリティ対応済みコンポーネント
- カスタマイズ性が高い

### 3.3 状態管理

**選定**: **Zustand / Jotai**

**理由**:
- シンプルで学習コスト低
- Redux不要（複雑なグローバル状態は少ない）

### 3.4 Markdownエディタ

**選定**: **CodeMirror 6 / TipTap**

**理由**:
- CodeMirror: Markdown専用、拡張性高
- TipTap: WYSIWYG対応、ユーザーフレンドリー

**Phase 1**: TipTap（ユーザビリティ優先）
**Phase 2**: CodeMirror検討（パワーユーザー向けオプション）

### 3.5 グラフ可視化

**選定**: **D3.js + React Flow / Cytoscape.js**

**用途**: 引用ネットワークグラフ

**選定**: React Flow（Reactとの統合が容易）

---

## 4. AI/ML

### 4.1 コンテンツモデレーション（Phase 1）

**選定**: **OpenAI Moderation API**

**理由**:
- 高精度（暴力/性的/差別的コンテンツ検出）
- API呼び出しのみで簡単
- コスト: $0.0001/1,000トークン（非常に安価）

**代替案**: Google Perspective API, Azure Content Safety

### 4.2 新規性判定（Phase 2）

#### 埋め込みモデル: **OpenAI text-embedding-3-large / Cohere Embed**

**理由**:
- 多言語対応
- 高精度
- コスト効率: OpenAI $0.13/1M tokens

#### 類似度計算: **コサイン類似度**

**実装**: NumPy/SciPy

### 4.3 自然言語処理（Phase 2+）

**選定**: **LangChain / LlamaIndex**

**用途**:
- 引用箇所の自動抽出
- 要約生成
- タグ自動付与

---

## 5. ブロックチェーン・Web3

### 5.1 外部アンカリング（Phase 3）

**選定**: **OpenTimestamps（無料） + Bitcoin（有料オプション）**

**理由**:
- OpenTimestamps: 無料で Bitcoin にアンカー
- コスト: 月額0円（OpenTimestamps）、500-3,000円（直接Bitcoin）

**ライブラリ**: `opentimestamps` (Python)

### 5.2 NFT発行（Phase 3）

**選定**: **Polygon / Optimism（Ethereum L2）**

**理由**:
- ガス代が安い（Polygonは数円）
- Ethereumエコシステムと互換
- OpenSeaで流通可能

**NFT規格**: ERC-721（個別NFT） / ERC-1155（セミファンジブル）

**用途**:
- 高評価な投稿のNFT化
- 画像・動画・音声等のメディアコンテンツNFT化
- 古典認定投稿の記念NFT

**ライブラリ**: Web3.py / Brownie / Hardhat

### 5.3 スマートコントラクト

**言語**: **Solidity 0.8.x**

**用途**:
- NFT Minting
- DAO ガバナンス（Phase 3後期）

**開発環境**: Hardhat + Ethers.js

---

## 6. Kindle出版（Phase 3）

### 6.1 EPUB生成

**選定**: **Pandoc / ebooklib (Python)**

**理由**:
- Markdown → EPUB変換が容易
- メタデータ埋め込み対応

### 6.2 KDP API統合

**注意**: Kindle Direct Publishing (KDP) は公式APIが限定的

**代替案**:
1. KDP Content API（限定公開、要申請）
2. 手動アップロードフロー（ユーザーがダウンロードしてKDPにアップ）

**Phase 3初期**: 手動フローで開始、需要次第でAPI申請

---

## 7. インフラ・DevOps

### 7.1 クラウドプロバイダ

**選定**: **AWS / GCP（選定中）**

**比較**:

| 項目 | AWS | GCP |
|------|-----|-----|
| コスト | やや高 | やや安 |
| エコシステム | 最大 | 良好 |
| AI/ML | SageMaker | Vertex AI（やや優位） |
| サポート | 最良 | 良好 |

**推奨**: **GCP**（AI統合が容易、コスト安）

### 7.2 コンテナ・オーケストレーション

**選定**: **Docker + Cloud Run / AWS Fargate**

**理由**:
- サーバーレスコンテナ（自動スケール）
- K8s不要（Phase 1-2は複雑さ回避）

**Phase 3**: Kubernetes検討（大規模化時）

### 7.3 CI/CD

**選定**: **GitHub Actions**

**理由**:
- GitHub統合
- 無料枠が大きい（パブリックリポジトリなら無制限）

**パイプライン**:
1. Lint/Format (ESLint, Prettier, Ruff, Black)
2. Unit Test
3. E2E Test (Playwright)
4. Build
5. Deploy（Staging → Production）

### 7.4 モニタリング・ログ

**選定**: **Datadog / New Relic / Google Cloud Monitoring**

**推奨**: **Google Cloud Monitoring**（GCP利用の場合、統合が容易）

**メトリクス**:
- API レスポンスタイム
- エラー率
- データベースパフォーマンス
- AI API使用量・コスト

**ログ**: Cloud Logging / CloudWatch Logs

### 7.5 CDN

**選定**: **Cloudflare / AWS CloudFront / Google Cloud CDN**

**推奨**: **Cloudflare**（無料プランが強力、DDoS対策含む）

---

## 8. 開発ツール

### 8.1 Monorepo管理

**選定**: **Turborepo / Nx**

**推奨**: **Turborepo**（シンプル、キャッシュ強力）

### 8.2 バージョン管理

**Git**: GitHub（Public Repository推奨、オープンソース化視野）

### 8.3 パッケージマネージャ

- **Backend**: Poetry (Python)
- **Frontend**: pnpm

### 8.4 コード品質

- **Linter**: ESLint (TS), Ruff (Python)
- **Formatter**: Prettier (TS), Black (Python)
- **Type Check**: TypeScript, mypy (Python)

### 8.5 テストフレームワーク

- **Backend**: pytest, pytest-asyncio
- **Frontend**: Vitest, React Testing Library
- **E2E**: Playwright

---

## 9. サードパーティAPI/SaaS

| 用途 | サービス | 月額コスト目安 |
|------|---------|---------------|
| 認証 | Supabase Auth | $25（1万MAU以下無料） |
| AI査読 | OpenAI Moderation | $1-10 |
| 埋め込み | OpenAI Embeddings | $50-200（Phase 2） |
| ベクトルDB | Pinecone | $70-（1M vectors） |
| ストレージ | Google Cloud Storage | $20-100 |
| CDN | Cloudflare | $0（無料プラン） |
| モニタリング | Google Cloud Monitoring | $50-150 |
| メール送信 | SendGrid / Resend | $15-（1万通/月） |
| アンカリング | OpenTimestamps | $0 |
| NFT Minting | Polygon | $数円/トランザクション |
| **合計（Phase 1）** | - | **$200-400/月** |

---

## 10. セキュリティ

### 10.1 認証・認可
- JWT（短寿命アクセストークン + リフレッシュトークン）
- HTTPS必須（Let's Encrypt）
- CORS設定

### 10.2 データ保護
- パスワード: bcrypt/Argon2
- 機密情報: AWS Secrets Manager / GCP Secret Manager
- GDPR対応: 匿名化API

### 10.3 API保護
- レート制限（Redis）
- SQL Injection対策（ORM使用: SQLAlchemy）
- XSS対策（React自動エスケープ + Content Security Policy）

### 10.4 監査
- アクセスログ保存（1年）
- 定期セキュリティスキャン（Snyk / Dependabot）

---

## 11. 技術スタック一覧（まとめ）

### Backend
```
Language: Python 3.12+
Framework: FastAPI 0.110+
Database: PostgreSQL 16, Redis 7
ORM: SQLAlchemy 2.x
Auth: Supabase Auth / Auth0
Queue: Celery + Redis
Storage: Google Cloud Storage / AWS S3
```

### Frontend
```
Language: TypeScript 5.x
Framework: React 18.x
Build Tool: Vite 5.x
UI: Tailwind CSS + shadcn/ui
State: Zustand
Editor: TipTap / CodeMirror 6
Graph: React Flow
```

### AI/ML
```
Moderation: OpenAI Moderation API
Embeddings: OpenAI text-embedding-3-large
Vector DB: Pinecone / Weaviate
Framework: LangChain (Phase 2+)
```

### Blockchain/Web3
```
Anchoring: OpenTimestamps + Bitcoin
NFT: Polygon (ERC-721/1155)
Smart Contract: Solidity 0.8.x
Tools: Hardhat + Ethers.js
```

### Infrastructure
```
Cloud: Google Cloud Platform
Container: Docker + Cloud Run
CI/CD: GitHub Actions
Monitoring: Google Cloud Monitoring
CDN: Cloudflare
```

### DevOps
```
Monorepo: Turborepo
Package Manager: Poetry (Python), pnpm (TS)
Linter: Ruff, ESLint
Formatter: Black, Prettier
Testing: pytest, Vitest, Playwright
```

---

## 12. 技術的負債の回避

### 12.1 Phase 1で避けるべき技術
- マイクロサービス化（複雑性増大）
- Kubernetes（運用コスト高）
- 自前認証実装（セキュリティリスク）
- GraphQL（REST APIで十分）

### 12.2 段階的導入
- Phase 1: モノリス + マネージドサービス
- Phase 2: 一部サービス分離（AI査読等）
- Phase 3: マイクロサービス化検討

---

## 13. コスト試算（Phase 1想定）

### 13.1 開発コスト
- エンジニア3名 x 6ヶ月 x 月額50万円 = **900万円**

### 13.2 インフラコスト（月額）
- Cloud Run: $50-100
- PostgreSQL (Cloud SQL): $50-100
- Redis (Memorystore): $30-50
- Storage: $20-50
- CDN (Cloudflare): $0
- 各種API (OpenAI等): $50-100
- **合計: $200-400/月（約3-6万円）**

### 13.3 年間ランニングコスト
- インフラ: 約40-70万円/年
- ドメイン/SSL: 約2万円/年
- 法務対応: 約10-30万円/年
- **合計: 約50-100万円/年**

---

## 14. 技術選定の変更基準

### 14.1 変更検討タイミング
- ユーザー数が10万人突破（スケールアップ）
- 特定技術のパフォーマンス問題
- コスト超過（月額50万円以上）
- セキュリティインシデント

### 14.2 代替技術の評価基準
1. パフォーマンス改善度
2. 移行コスト
3. 長期保守性
4. チームのスキルセット

---

## 15. 次のステップ

1. GCP vs AWS 最終決定（1週間以内）
2. リポジトリ初期化（Turborepo設定）
3. 開発環境構築（Docker Compose）
4. 最初のAPI実装（User登録）

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 著者 |
|-----------|------|---------|------|
| 1.0 | 2026-03-24 | 初版作成 | - |
