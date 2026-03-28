# オリジナリティ査読システム実装設計

## 概要

Lighthouse Protocolに基づき、2層の査読システムを実装する。
**査読1（LLM自動査読）を突破した投稿のみが、査読2（ユーザー査読）に進み、最終的に「Public作品」として永続化される。**

## Lighthouse Protocolの査読思想

### LLM査読の本質
LLMは「平均的な正解を出す装置」ではなく、**「平均からの乖離を検知するセンサー」**として機能する。

### 評価軸（The Scoring Engine）

1. **乖離度 (Divergence)**
   - 既存のWebデータや標準的なAI回答から、意味ベクトルがどれだけ離れているか
   - Embeddings類似度の逆数として計算

2. **内部密度 (Density)**
   - 乖離した「特異点」において、具体的かつ論理的な補強がどれだけ集中しているか
   - 5W1H、微細な観察、矛盾する感情等の一次情報の濃度

3. **逆シミュレーション (Reverse Simulation)**
   - 別のLLMに続きを書かせ、AIが予測できない「人間固有の執着・跳躍」が含まれているかを検証

4. **AI生成物の許容**
   - AIを用いた創作であっても、人類の知に貢献する「独自性」があれば正当にアーカイブ

---

## 実装アーキテクチャ

### Phase 1: LLM自動査読（必須・即時）

投稿時に以下のチェックを**順次実行**し、いずれかに引っかかった時点で投稿を拒否またはprivateに降格。

#### 1.1 コンテンツモデレーション（安全性チェック）
**目的:** 暴力的・性的・差別的コンテンツの排除
**実装:** OpenAI Moderation API（既存実装）
**判定:**
- REJECTED → 投稿拒否（下書き保存、フィードバック表示）
- APPROVED → 次のチェックへ

#### 1.2 既存投稿との類似度チェック
**目的:** プラットフォーム内での重複投稿・盗用の検出
**実装:**
- OpenAI `text-embedding-3-small` でテキストをベクトル化（1536次元）
- PostgreSQL pgvector でコサイン類似度を計算
- 類似度 > 0.90 → 「ほぼ同一の投稿が存在」として警告
- 類似度 0.85-0.90 → 「類似投稿あり」として警告（投稿は許可）

**SQL例:**
```sql
SELECT id, content, 1 - (content_embedding <=> $1) AS similarity
FROM outputs
WHERE 1 - (content_embedding <=> $1) > 0.85
ORDER BY similarity DESC
LIMIT 5
```

#### 1.3 Web上の既存文章チェック
**目的:** インターネット上の既存著作物（小説、論文、記事）からの盗用検出
**実装:**
- Google Custom Search API を使用
- 文章から特徴的なフレーズ（50-100文字）を複数抽出
- 完全一致または高い類似度でヒット → 「既存文章の可能性」として警告

**抽出ロジック:**
```python
# 文章を3等分し、各セクションから特徴的なフレーズを抽出
def extract_search_phrases(content: str, num_phrases: int = 3) -> list[str]:
    # 句読点で分割し、50-100文字のフレーズを抽出
    # 固有名詞や具体的な描写を含むフレーズを優先
```

#### 1.4 AI生成物検出 + オリジナリティ判定
**目的:** AI生成コンテンツの検出と、その上でのオリジナリティ評価
**実装:** GPT-4o による複合判定

**プロンプト設計:**
```
以下のテキストを分析し、3つの観点から評価してください:

1. AI生成確率（0-100%）
   - ChatGPT/Claude等のLLM特有のパターン（定型表現、構造、語彙）

2. 既存著作物の可能性（0-100%）
   - 既知の小説、論文、記事等からの引用・模倣の可能性
   - 具体的な作品名が判明する場合は提示

3. オリジナリティスコア（0-100点）
   - AI生成であっても、独自の視点・洞察・論理展開があれば高評価
   - 一次情報（具体的観察、個人的体験、独自データ）の濃度
   - 「平均からの乖離」と「内部密度」を総合評価

テキスト:
---
{content}
---

JSON形式で回答:
{
  "ai_generated_probability": 0-100,
  "existing_work_probability": 0-100,
  "suspected_source": "作品名またはnull",
  "originality_score": 0-100,
  "reasoning": "判定理由の簡潔な説明"
}
```

**判定基準:**
- `existing_work_probability > 70` かつ `suspected_source != null` → 「既存著作物の可能性」として警告
- `ai_generated_probability > 80` かつ `originality_score < 30` → 「AI生成で独自性不足」として警告
- `originality_score >= 60` → 査読通過（AI生成でもOK）
- `originality_score < 60` → Private降格（フォロワー限定）

#### 1.5 逆シミュレーション（オプション・高負荷）
**目的:** 「AIが予測できない人間固有の執着・跳躍」の検出
**実装:** GPT-4o に続きを書かせて、実際の続き（ユーザーが書いた場合）と比較

**フロー:**
1. 投稿の前半70%をGPT-4に渡し、続きを生成
2. 実際の後半30%とEmbeddings類似度を比較
3. 類似度 < 0.70 → 「予測不可能な展開」として高評価
4. 類似度 > 0.85 → 「AIが容易に予測できる内容」として減点

**Phase 1実装優先度:**
- **P0（即時実装）:** 1.1, 1.2, 1.3, 1.4
- **P1（Phase 2）:** 1.5（計算コスト高）

---

### Phase 2: ユーザー査読（将来実装）

**現在のスコープ外**
Phase 1で査読通過（`originality_score >= 60`）した投稿は、自動的にPublicとして公開される。

将来的には：
- 複数ユーザーによるピアレビュー
- 「引用」による間接的評価
- 批判・改善提案による「共同貢献者」認定

---

## 実装ステップ

### Step 1: インフラ準備
- [x] PostgreSQL pgvector拡張のセットアップ（docker-compose.yml更新）
- [ ] Alembic migration実行（`content_embedding`カラム追加）
- [ ] Google Custom Search API キー取得・設定

### Step 2: ユーティリティ実装
- [ ] `app/utils/embeddings.py` - Embeddings生成
- [ ] `app/utils/similarity_search.py` - pgvector類似度検索
- [ ] `app/utils/web_search.py` - Google検索
- [ ] `app/utils/originality_check.py` - GPT-4判定 + 総合評価

### Step 3: 投稿フロー統合
- [ ] `app/routers/outputs.py` 修正
  - 既存の`check_content_safety`の後に新しいチェックを追加
  - `originality_score`をDBに保存
  - スコア < 60 → Private降格
  - 警告メッセージを日本語で生成

### Step 4: フロントエンド対応
- [ ] 警告メッセージUI（類似投稿、既存文章、AI生成）
- [ ] Originality Scoreの表示（任意）

---

## データモデル拡張

### `outputs`テーブル追加カラム

```sql
ALTER TABLE outputs ADD COLUMN content_embedding vector(1536);  -- Embeddings
ALTER TABLE outputs ADD COLUMN originality_score INTEGER;        -- 0-100
ALTER TABLE outputs ADD COLUMN ai_generated_probability INTEGER; -- 0-100
ALTER TABLE outputs ADD COLUMN originality_warnings TEXT[];      -- 警告メッセージ配列
```

---

## API設定要件

### 必須API
1. **OpenAI API**（既存）
   - Moderation API
   - Embeddings API: `text-embedding-3-small`
   - Chat API: `gpt-4o` または `gpt-4o-mini`

2. **Google Custom Search API**（新規）
   - Custom Search JSON API
   - 1日100クエリまで無料、その後$5/1000クエリ

### 環境変数追加

```bash
# Google Custom Search
GOOGLE_CUSTOM_SEARCH_API_KEY=xxx
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=xxx

# Originality Check Settings
ORIGINALITY_THRESHOLD=60  # 0-100, この値未満はPrivate
SIMILARITY_THRESHOLD=0.85 # 0-1, この値以上は類似警告
```

---

## コスト見積もり

### OpenAI API
- **Embeddings（text-embedding-3-small）:** $0.02 / 1M tokens
  - 1投稿500文字 ≈ 200 tokens → $0.000004/投稿
- **GPT-4o判定:** $2.50 / 1M input tokens, $10.00 / 1M output tokens
  - 1投稿500文字入力 + 150文字出力 ≈ $0.0007/投稿

### Google Custom Search
- 無料枠: 100クエリ/日
- 超過分: $5 / 1000クエリ

### 合計
**1投稿あたり約$0.0007（0.1円）** + Google検索コスト

---

## 今後の最適化

### Phase 3: パフォーマンス改善
1. **キャッシング**
   - 同一コンテンツのEmbeddings再利用（content_hashベース）
   - Google検索結果のRedisキャッシュ（24時間）

2. **バッチ処理**
   - Embeddings生成をバックグラウンドジョブ化
   - 類似度検索の並列化

3. **閾値チューニング**
   - ユーザーフィードバックに基づき閾値を調整
   - A/Bテストでオリジナリティスコアの有効性を検証

---

## 実装スケジュール

| フェーズ | タスク | 見積もり |
|---------|--------|---------|
| Phase 1.1 | インフラ準備 + Migration | 1-2時間 |
| Phase 1.2 | Embeddings + 類似度検索 | 2-3時間 |
| Phase 1.3 | Web検索実装 | 1-2時間 |
| Phase 1.4 | GPT-4判定実装 | 2-3時間 |
| Phase 1.5 | 投稿フロー統合 | 2-3時間 |
| Phase 1.6 | フロントエンド対応 | 1-2時間 |
| **合計** | | **9-15時間** |

---

## リスクと対策

### リスク1: 誤検知（False Positive）
**対策:**
- 閾値を保守的に設定（初期は緩め）
- 警告のみで投稿を許可するオプション
- ユーザーからの異議申し立て機能（Phase 2）

### リスク2: APIコスト増加
**対策:**
- レート制限（1ユーザー1日10投稿まで）
- 短文（<50文字）はオリジナリティチェックをスキップ
- Embeddingsキャッシング

### リスク3: パフォーマンス劣化
**対策:**
- 非同期処理（投稿は即座に受付、査読は裏で実行）
- ステータス: `PENDING_REVIEW` → `APPROVED` / `REJECTED`
- WebSocket/SSEで結果を通知

---

## 次のアクション

1. このドキュメントのレビュー・承認
2. Google Custom Search APIのセットアップ
3. Step 1（インフラ準備）から順次実装開始
