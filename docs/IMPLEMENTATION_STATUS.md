# 実装状況サマリー

**最終更新日**: 2026-03-25
**プロジェクト**: Lighthouse of Intellect（知の灯台）

---

## ✅ 実装済み機能（Phase 1）

### 1. 認証・ユーザー管理
- [x] JWT認証
- [x] ユーザー登録（メールアドレス）
- [x] ログイン/ログアウト
- [x] ソーシャルログイン（Google OAuth）
- [x] ソーシャルログイン（LINE OAuth）
- [x] プロフィール編集

### 2. 投稿機能（Output）
- [x] 投稿作成
- [x] 投稿編集
- [x] 投稿一意ID生成（OUT-YYYY-MMDD-HASH形式）
- [x] カテゴリ管理（science, art, philosophy, technology, society, script, place, experience, other）
- [x] タグ機能
- [x] 投稿詳細表示
- [x] 投稿一覧（タイムライン）

### 3. ハッシュチェーン（不可逆性）
- [x] SHA-256ハッシュ生成
- [x] Content Hash（コンテンツのみ）
- [x] Full Hash（コンテンツ + メタデータ + タイムスタンプ）
- [x] Previous Hash（編集履歴チェーン）
- [x] Version管理
- [x] **ハッシュ検証エンドポイント（Public Outputのみ）**
- [x] 編集履歴（OutputHistory）の保存

### 4. 引用システム
- [x] 引用作成API
- [x] 引用タイプ（agree, criticize, develop, reference）
- [x] 引用の抜粋（excerpt）
- [x] 被引用一覧取得（Cited By）
- [x] 引用一覧取得（Cites）
- [x] 引用統計（incoming/outgoing citations, タイプ別内訳）
- [x] 引用グラフAPI
- [x] **フロントエンドUI（引用表示、引用作成フロー）**

### 5. フォローシステム
- [x] ユーザーフォロー/アンフォロー
- [x] フォロワー一覧
- [x] フォロー中一覧
- [x] フォロー統計
- [x] **Outputフォロー機能**（投稿単位のフォロー）

### 6. Agreement（同意見）機能
- [x] 同意見追加/取り消し
- [x] 同意見数カウント
- [x] 同意見ユーザー一覧

### 7. Lighthouse Protocol実装
- [x] **プロトコル同意機能**（has_agreed_to_protocol）
- [x] プロトコルドキュメント表示モーダル
- [x] 初回投稿時の同意チェック

### 8. AI査読システム（Phase 1: 安全性チェック + オリジナリティ判定）

#### 8.1 コンテンツモデレーション
- [x] OpenAI Moderation API統合
- [x] 暴力的・性的・差別的コンテンツの検出
- [x] 日本語フィードバックメッセージ生成
- [x] 却下投稿の再編集フロー（フロントエンド統合）

#### 8.2 オリジナリティチェック（Lighthouse Protocol - 査読1）
- [x] **Embeddings生成** - OpenAI text-embedding-3-small (1536次元)
- [x] **類似度検索** - PostgreSQL pgvector + HNSW index
- [x] **Web検索** - Google Custom Search API（盗用検出）
- [x] **LLM判定** - GPT-4o による総合判定
  - AI生成確率判定（0-100%）
  - 既存著作物検出
  - オリジナリティスコア算出（0-100点）
- [x] Public/Private自動振り分け（スコア60点基準）
- [x] 警告メッセージ生成・表示
- [x] フロントエンド統合（スコア・警告表示）

### 9. 場所・作品レビュー機能
- [x] Google Places API統合
- [x] 場所検索エンドポイント
- [x] 場所詳細取得エンドポイント
- [x] referenced_entity フィールド（type, id, data）
- [x] EntitySearchModal コンポーネント
- [x] 投稿作成時の場所紐付け
- [x] タイムライン・詳細ページでの場所情報表示

### 10. 検索機能
- [x] PostgreSQL Full-text Search設定（GIN index）
- [x] 投稿全文検索準備（インデックス作成済み）
- [ ] 投稿全文検索API実装
- [ ] タグ検索
- [ ] ユーザー検索

### 11. 通知機能
- [x] 通知テーブル作成
- [x] 通知スキーマ定義
- [ ] フォロー通知実装
- [ ] 引用通知実装
- [ ] 同意見通知実装
- [ ] フロントエンド通知UI

---

## 🚧 未実装機能

### Phase 1 残タスク

#### 通知機能（実装中）
- [ ] 通知API実装（作成・取得・既読管理）
- [ ] リアルタイム通知（WebSocket/SSE）
- [ ] 通知UI（ベル アイコン、ドロップダウン）

#### 検索機能（実装中）
- [ ] 投稿全文検索API
- [ ] タグ検索
- [ ] ユーザー検索

### Phase 2: Lighthouse Protocol高度化

#### 査読1（LLM自動査読）の高度化
- [x] **乖離度（Divergence）判定** - 埋め込みベクトルによる類似度検索（実装済み）
- [x] **内部密度（Density）判定** - GPT-4oによる一次情報密度評価（実装済み）
- [ ] **逆シミュレーション** - AI予測不能性の検証（高度な乖離度判定）
- [x] オリジナリティスコア算出（0-100点、実装済み）
- [x] ベクトルデータベース（PostgreSQL pgvector、実装済み）
- [ ] スコアリングアルゴリズムのチューニング
- [ ] 閾値の最適化（A/Bテスト）

#### 査読2（ユーザーピアレビュー）
- [ ] ピアレビュー投票システム
- [ ] レビュアー選定アルゴリズム
- [ ] レビュー実績スコア（Reviewer Reputation）
- [ ] Private → Public昇格フロー
- [ ] 異議申立てAPI

#### Public/Private Output分離
- [x] オリジナリティ判定による自動振り分け（実装済み）
- [ ] Private Output閲覧制限（フォロワーのみ）
- [ ] Private Output専用タイムライン
- [ ] Public昇格リクエスト機能

#### フィードバック・コーチング
- [x] オリジナリティ警告メッセージ（実装済み）
- [ ] **不採用時のメンター機能** - LLMによる詳細な改善提案
- [ ] 再投稿時の差分分析
- [ ] 論理強化スコア可視化
- [ ] 成長トラッキング（スコア推移グラフ）

#### 批判の価値化
- [ ] **共同貢献者（Contributor）記録** - 批判による改善の追跡
- [ ] 批判品質スコア
- [ ] 編集履歴への貢献者表示

#### 引用グラフ可視化
- [ ] D3.js/Cytoscape.js実装
- [ ] インタラクティブ操作（ズーム/パン/ノードクリック）
- [ ] グラフレイアウトアルゴリズム最適化

#### サジェストアルゴリズム
- [ ] PageRankアルゴリズム実装
- [ ] 引用品質スコア計算
- [ ] 時系列減衰ロジック
- [ ] サジェストフィードAPI

### Phase 3: エコシステム

#### 外部アンカリング
- [ ] Bitcoin/Ethereum ノード統合
- [ ] OpenTimestamps統合
- [ ] 1日1回アンカリングバッチ
- [ ] アンカリング履歴公開API

#### 称号・アワードシステム
- [ ] **LLMによる二つ名授与**（「論理の外科医」等）
- [ ] **ジャイアント・キリング記録** - 無名が権威を突く歴史的転換点
- [ ] 古典認定基準アルゴリズム
- [ ] 年間アワード投票システム

#### DAO移行
- [ ] DAOフレームワーク選定
- [ ] ガバナンストークン設計
- [ ] スマートコントラクト実装
- [ ] 投票システム統合

---

## 📊 プロトコル実装優先度

### 最優先（Phase 1完了前に実装すべき）

| 要件ID | 機能 | 理由 |
|--------|------|------|
| FR-LH-060 | 削除不可同意プロセス | プロトコルの根幹。法的リスク回避 |
| FR-LH-010 | ブラインド審査 | 権威性排除の実現 |
| FR-LH-051 | 権威性メトリクス排除UI | フォロワー数の過度な強調を防ぐ |

### 高優先度（Phase 2前半）

| 要件ID | 機能 | 理由 |
|--------|------|------|
| FR-LH-001 | 乖離度判定 | 新規性判定の核心 |
| FR-LH-002 | 内部密度判定 | 具体性評価の実現 |
| FR-LH-040 | メンター機能 | ユーザー育成の鍵 |

### 中優先度（Phase 2後半）

| 要件ID | 機能 | 理由 |
|--------|------|------|
| FR-LH-003 | 逆シミュレーション | より高度な新規性判定 |
| FR-LH-020 | 批判の価値化 | 建設的批判の促進 |
| FR-LH-021 | 批判品質スコア | 質の高い批判を評価 |

### 低優先度（Phase 3）

| 要件ID | 機能 | 理由 |
|--------|------|------|
| FR-LH-030 | 二つ名授与 | ゲーミフィケーション要素 |
| FR-LH-050 | ジャイアント・キリング | 歴史的記録としての価値 |
| FR-LH-011 | ブラインドフィード | オプション機能 |

---

## 🗂️ データベーススキーマ追加必要事項

### すぐに必要
```sql
-- User同意管理
ALTER TABLE users ADD COLUMN has_agreed_to_protocol BOOLEAN DEFAULT FALSE;

-- 引用グラフ用インデックス（既存データに対して）
CREATE INDEX IF NOT EXISTS idx_citations_source_target ON citations(source_output_id, target_output_id);
```

### Phase 2で必要
```sql
-- LLM二つ名
ALTER TABLE users ADD COLUMN title VARCHAR(100);
ALTER TABLE users ADD COLUMN logic_enhancement_score FLOAT DEFAULT 0;

-- 批判貢献者
ALTER TABLE output_history ADD COLUMN contributor_ids UUID[];

-- AI査読フィードバック
CREATE TABLE ai_review_feedback (
    id UUID PRIMARY KEY,
    output_id VARCHAR(30) REFERENCES outputs(id),
    divergence_score FLOAT,
    density_score FLOAT,
    reverse_simulation_score FLOAT,
    feedback_text TEXT,
    improvement_suggestions TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Phase 3で必要
```sql
-- ジャイアント・キリング
CREATE TABLE giant_killing_events (
    id UUID PRIMARY KEY,
    challenger_output_id VARCHAR(30) REFERENCES outputs(id),
    target_output_id VARCHAR(30) REFERENCES outputs(id),
    challenger_user_id UUID REFERENCES users(id),
    target_user_id UUID REFERENCES users(id),
    support_count INT DEFAULT 0,
    detected_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 外部アンカリング
CREATE TABLE hash_anchors (
    id UUID PRIMARY KEY,
    root_hash VARCHAR(64) NOT NULL,
    blockchain VARCHAR(20) NOT NULL,
    transaction_id VARCHAR(100),
    anchored_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📈 技術的負債と改善点

### パフォーマンス
- [ ] 引用グラフ生成の最適化（現在のBFS実装は深度5まで非効率）
- [ ] ベクトル検索の導入（類似投稿検索の高速化）
- [ ] キャッシュ戦略の強化（Redis活用）

### セキュリティ
- [ ] レート制限の実装（引用スパム防止）
- [ ] CSRF保護の強化
- [ ] XSS対策の監査

### コード品質
- [ ] バックエンドユニットテストカバレッジ向上（現状: 不明 → 目標: 80%）
- [ ] フロントエンドテスト追加
- [ ] E2Eテスト（Playwright）

---

## 🚀 次のマイルストーン

### M1: Phase 1 完全完了（目標: 1ヶ月以内）
- [ ] AI査読（コンテンツモデレーション）実装
- [ ] 検索機能実装
- [ ] 通知機能実装
- [ ] **削除不可同意プロセス実装**（プロトコル）
- [ ] ユニットテストカバレッジ80%達成

### M2: Lighthouse Protocol Phase 1（目標: 2-3ヶ月）
- [ ] ブラインド審査実装
- [ ] 乖離度判定実装
- [ ] 内部密度判定実装
- [ ] メンター機能実装
- [ ] Public/Private自動振り分け

### M3: エコシステム基盤（目標: 6ヶ月）
- [ ] 引用グラフ可視化
- [ ] PageRankアルゴリズム
- [ ] 批判の価値化
- [ ] サジェストフィード

---

## 📝 ドキュメント整備状況

### ✅ 完成済み
- [x] プロトコル定義書（`the_lighthouse_protocol.md`）
- [x] Lighthouse Protocol実装要件（`lighthouse-protocol-requirements.md`）
- [x] 機能要件定義（`requirements.md`）
- [x] タスク分解書（`task-breakdown.md`）
- [x] 技術スタック選定（`tech-stack.md`）
- [x] システムアーキテクチャ（`architecture.md`）

### 🚧 未完成・要更新
- [ ] API設計書の更新（引用API等の追加仕様）
- [ ] データベース詳細設計（ER図更新）
- [ ] LLM査読アーキテクチャ設計書（新規作成）
- [ ] フロントエンドコンポーネント設計書
- [ ] デプロイ手順書

---

## 🎯 重要な設計判断

### 1. ハッシュチェーンの実装方式
- **決定**: PostgreSQL内部でハッシュ管理、外部アンカリングは後回し
- **理由**: Phase 1での素早いリリースを優先。ブロックチェーン統合はPhase 3
- **トレードオフ**: 完全な分散化は遅れるが、内部整合性は保証される

### 2. AI査読の段階的実装
- **Phase 1**: コンテンツモデレーションのみ（暴力・性的・差別）
- **Phase 2**: 新規性判定（乖離度・密度・逆シミュレーション）
- **理由**: LLM APIコストとアルゴリズム検証に時間が必要

### 3. プロトコル同意の実装タイミング
- **決定**: Phase 1完了前に実装必須
- **理由**: 法的リスク。後から追加すると既存ユーザーの同意取得が困難

---

## 🔄 継続的改善

このドキュメントは実装状況に応じて定期的に更新されます。
**次回更新予定**: Phase 1完了時（AI査読・検索実装後）

### 更新履歴
- 2026-03-25: 初版作成（ハッシュチェーン・引用機能実装完了時点）
- 2026-03-25 (更新): オリジナリティチェックシステム実装完了（査読1）

---

## 📦 最新実装: オリジナリティチェックシステム

**実装日**: 2026-03-25
**ステータス**: ✅ 完了

### アーキテクチャ概要

Lighthouse Protocolの中核機能である**査読1（LLM自動査読）**を実装しました。4層のチェックシステムにより、独自性・新規性・一次性を評価します。

```
投稿作成
  ↓
[1] コンテンツモデレーション（OpenAI Moderation API）
  ↓ 安全性OK
[2] Embeddings生成（text-embedding-3-small, 1536次元）
  ↓
[3] 類似度検索（pgvector + HNSW index, cosine similarity > 0.85）
  ↓
[4] Web検索（Google Custom Search API, 3フレーズ × 3結果）
  ↓
[5] LLM総合判定（GPT-4o）
  - AI生成確率（0-100%）
  - 既存著作物検出
  - オリジナリティスコア（0-100点）
  ↓
[6] Public/Private振り分け（スコア60点基準）
```

### 技術スタック

| レイヤー | 技術 | 用途 |
|---------|------|------|
| Embeddings | OpenAI text-embedding-3-small | 1536次元ベクトル生成 |
| Vector DB | PostgreSQL pgvector | コサイン類似度検索 |
| Index | HNSW (Hierarchical Navigable Small World) | 高速近似最近傍探索 |
| Web Search | Google Custom Search API | 盗用・既存著作物検出 |
| LLM Judge | OpenAI GPT-4o | 総合的オリジナリティ判定 |

### データベーススキーマ

```sql
-- outputs テーブルに追加されたカラム
ALTER TABLE outputs ADD COLUMN content_embedding vector(1536);
ALTER TABLE outputs ADD COLUMN originality_score INTEGER;
ALTER TABLE outputs ADD COLUMN ai_generated_probability INTEGER;
ALTER TABLE outputs ADD COLUMN originality_warnings TEXT[];

-- HNSW インデックス（高速ベクトル検索）
CREATE INDEX idx_outputs_content_embedding_hnsw
ON outputs USING hnsw (content_embedding vector_cosine_ops);

-- pgvector 拡張
CREATE EXTENSION IF NOT EXISTS vector;
```

### マイグレーション

1. **20260325_1500_add_pgvector_and_embedding.py**
   - pgvector拡張の有効化
   - content_embeddingカラム追加（vector(1536)）
   - HNSWインデックス作成

2. **20260325_1600_add_originality_fields.py**
   - originality_scoreカラム追加（INTEGER, 0-100）
   - ai_generated_probabilityカラム追加（INTEGER, 0-100）
   - originality_warningsカラム追加（TEXT[]）

### 実装ファイル

#### バックエンド

| ファイル | 役割 |
|---------|------|
| `app/utils/embeddings.py` | OpenAI Embeddings API ラッパー |
| `app/utils/similarity_search.py` | pgvector コサイン類似度検索 |
| `app/utils/web_search.py` | Google Custom Search API統合 |
| `app/utils/originality_check.py` | GPT-4o 総合判定ロジック |
| `app/routers/outputs.py` | 投稿作成フローへの統合 |
| `app/models/output.py` | Outputモデル拡張 |
| `app/schemas/output.py` | Pydanticスキーマ拡張 |
| `app/config.py` | Google Custom Search設定追加 |

#### フロントエンド

| ファイル | 役割 |
|---------|------|
| `src/lib/api.ts` | Output型定義にオリジナリティフィールド追加 |
| `src/pages/CreateOutput.tsx` | 拒否/警告メッセージ表示 |
| `src/pages/OutputDetail.tsx` | スコア・警告表示UI |

#### ドキュメント

| ファイル | 役割 |
|---------|------|
| `docs/design/originality-check-implementation.md` | 詳細設計書 |
| `TESTING_GUIDE.md` | テスト手順書 |

### パフォーマンス指標

**想定API呼び出し時間（投稿1件あたり）:**

- Embeddings生成: 200-500ms
- pgvector類似度検索: 50-200ms
- Google Web検索: 500-1500ms
- GPT-4o判定: 2-5秒

**合計**: 約3-7秒

**API コスト（1,000投稿あたり）:**

- Embeddings: $0.004
- GPT-4o: $0.70
- Google Custom Search: $5.00 (無料枠超過時)

**合計**: ~$5.70

### 設定

`.env` に以下を追加:

```bash
# OpenAI API
OPENAI_API_KEY=sk-...

# Google Custom Search API
GOOGLE_CUSTOM_SEARCH_API_KEY=...
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=...
```

### テスト方法

詳細は `TESTING_GUIDE.md` を参照。

**主要テストケース:**
1. オリジナルコンテンツ → Public承認（スコア70-90）
2. 盗用コンテンツ（太宰治「芸術ぎらい」） → Private降格（スコア<30）
3. AI生成汎用コンテンツ → Private降格（AI確率>80%）
4. 類似投稿検出 → 警告表示
5. Web検索マッチ → 警告表示

### 今後の改善点

- [ ] 閾値のA/Bテスト（スコア60点が最適か検証）
- [ ] 埋め込みベクトルのキャッシュ（Redis）
- [ ] バッチ処理による高速化
- [ ] カスタムファインチューニングモデル
- [ ] 逆シミュレーション（Phase 2）
