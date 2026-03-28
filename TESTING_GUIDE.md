# Originality Check System - Testing Guide

## Overview

This guide provides step-by-step instructions for testing the newly implemented originality checking system based on the Lighthouse Protocol.

## Prerequisites

Before testing, you need to complete the following setup:

### 1. Environment Variables

Add the following to your `.env` file in `packages/backend/`:

```bash
# OpenAI API (Required)
OPENAI_API_KEY=sk-...  # Your OpenAI API key

# Serper API (Required for web plagiarism detection)
SERPER_API_KEY=...  # Your Serper API key

# Originality Threshold (Optional - defaults to 60)
ORIGINALITY_THRESHOLD=60
SIMILARITY_THRESHOLD=0.85
```

#### How to Get Serper API Key

1. **Sign up for Serper API:**
   - Go to [Serper.dev](https://serper.dev/)
   - Click "Sign Up" or "Get Started"
   - Create an account (GitHub login available)

2. **Get API Key:**
   - After logging in, go to API Keys section
   - Copy your API key
   - Free tier includes 2,500 queries/month

3. **Add to .env:**
   - Add `SERPER_API_KEY=your_key_here` to `.env` file

### 2. Database Migration

Run the Alembic migrations to add the required columns:

```bash
cd packages/backend

# Apply pgvector extension and embedding column
poetry run alembic upgrade head
```

This will create:
- `content_embedding` (vector(1536)) - Embedding vectors for similarity search
- `originality_score` (INTEGER) - Originality score (0-100)
- `ai_generated_probability` (INTEGER) - AI generation probability (0-100%)
- `originality_warnings` (TEXT[]) - Warning messages

### 3. Install Dependencies

Ensure pgvector and Google API client are installed:

```bash
cd packages/backend
poetry install
```

### 4. Restart Services

```bash
docker-compose down
docker-compose up -d
```

---

## Test Cases

### Test 1: Original Content (Should Pass)

**Objective:** Verify that genuinely original content gets high originality score and is approved as Public.

**Steps:**
1. Navigate to "Create Output" page
2. Enter the following content:
   ```
   私の祖母は昨日、85歳の誕生日を迎えました。彼女は戦後の混乱期に生まれ、
   高度経済成長期に若者だった世代です。私が最も印象に残っているのは、
   祖母が語ってくれた戦後直後の食糧難の話です。

   当時、祖母の家族は東京の下町に住んでいました。食べ物を手に入れるために、
   毎日のように近所の農家まで歩いて物々交換をしていたそうです。
   祖母は「着物を一枚出せば、お米が少しもらえた」と言っていました。

   この経験から、祖母は「物を大切にする」という価値観を強く持つようになりました。
   今でも、私が何かを無駄にしようとすると、必ず注意されます。
   ```
3. Category: "experience" (体験)
4. Submit

**Expected Result:**
- ✅ Output created successfully
- Originality Score: 70-90/100 (high score due to first-hand experience)
- Visibility: **Public**
- AI Generated Probability: Low (< 50%)
- No warnings about plagiarism

---

### Test 2: Plagiarized Content (Should Fail)

**Objective:** Verify that plagiarized content from known works is detected and rejected or demoted.

**Steps:**
1. Navigate to "Create Output" page
2. Enter content from a well-known work (e.g., 太宰治の「芸術ぎらい」):
   ```
   芸術はいやだ。人を酔わせて、ますます弱虫にするばかりだ。
   酔って、ころんで、泣いて、それでもう満足して、この現実の
   地べたの上には、何ひとつ変化が起っていないんだ。
   ```
3. Category: "philosophy"
4. Submit

**Expected Result:**
- ⚠️ Output saved as **Private** or rejected
- Originality Score: < 30/100
- Warning message: 「既存著作物の可能性: この内容は『芸術ぎらい』等からの引用・盗用の可能性があります」
- Error or feedback shown to user with option to edit

---

### Test 3: AI-Generated Generic Content (Should Be Demoted)

**Objective:** Verify that generic AI-generated content gets low originality score.

**Steps:**
1. Use ChatGPT or Claude to generate generic content:
   ```
   人工知能の発展は、私たちの社会に大きな影響を与えています。
   これは非常に重要な問題であり、慎重に考える必要があります。

   まず第一に、AIは多くの利点をもたらします。効率性の向上、
   コスト削減、そして新しい可能性の創出などが挙げられます。

   しかしながら、懸念すべき点も存在します。雇用の減少、
   プライバシーの問題、そして倫理的な課題などです。

   結論として、AIの発展は避けられないものですが、
   そのリスクと利益をバランスよく考慮することが重要です。
   ```
2. Category: "technology"
3. Submit

**Expected Result:**
- Output saved as **Private**
- Originality Score: 20-40/100 (low due to generic structure and typical AI phrases)
- AI Generated Probability: > 80%
- Warning: 「AI生成コンテンツで独自性が不足しています」
- Feedback: 「オリジナリティスコア XX点（基準60点未満）のため、Private投稿として保存されます」

---

### Test 4: Similar Content Detection (Internal Database)

**Objective:** Verify that similar posts are detected via embedding similarity.

**Steps:**
1. Create a first post with unique content:
   ```
   量子コンピュータの基本原理は、量子ビット（qubit）という概念に基づいています。
   古典的なビットが0か1のいずれかの状態を取るのに対し、量子ビットは重ね合わせ状態を
   取ることができます。
   ```
2. Wait for it to be created
3. Create a second post with very similar content (slight modifications):
   ```
   量子コンピュータの基礎となる原理は、キュービット（qubit）という考え方に基づいています。
   従来のビットが0または1のどちらかの状態であるのに対して、キュービットは重ね合わせの
   状態を持つことが可能です。
   ```
4. Submit

**Expected Result:**
- Warning: 「⚠️ 類似投稿: 既存の投稿『量子コンピュータの基本原理は...』と XX%の類似度があります」
- Originality Score may be reduced
- Possible demotion to Private depending on similarity level

---

### Test 5: Web Search Detection

**Objective:** Verify that content matching web sources is detected.

**Steps:**
1. Copy a distinctive paragraph from a published web article (e.g., Wikipedia, news site)
2. Paste it as output content
3. Submit

**Expected Result:**
- Warning: 「⚠️ Web上の類似コンテンツ: X件の類似する内容がインターネット上で見つかりました」
- LLM may also detect existing work probability
- Possible demotion to Private

---

### Test 6: Edge Case - Short Content

**Objective:** Verify handling of very short content (edge case).

**Steps:**
1. Enter very short content (< 50 characters):
   ```
   今日はいい天気だ。
   ```
2. Submit

**Expected Result:**
- Output may be created without extensive originality checking
- Or: Warning about insufficient content length
- System should handle gracefully without errors

---

### Test 7: API Error Handling

**Objective:** Verify graceful degradation when APIs are unavailable.

**Steps:**
1. Temporarily remove `OPENAI_API_KEY` from `.env`
2. Restart backend
3. Create a post

**Expected Result:**
- Post is created successfully (fails gracefully)
- Default behavior: Approved without originality checking
- Console warnings: "⚠️ OPENAI_API_KEY not set - skipping embedding generation"

---

## Verification Checklist

After running the tests, verify the following:

### Database Verification

```sql
-- Check that originality fields are populated
SELECT
    id,
    originality_score,
    ai_generated_probability,
    originality_warnings,
    visibility
FROM outputs
ORDER BY created_at DESC
LIMIT 5;

-- Check that embeddings are stored
SELECT
    id,
    array_length(content_embedding, 1) as embedding_dimensions
FROM outputs
WHERE content_embedding IS NOT NULL
LIMIT 5;
```

### Frontend Verification

1. **Create Output Page:**
   - Error messages display properly for rejected content
   - Warnings show for demoted-to-private content
   - User can edit and re-submit

2. **Output Detail Page:**
   - Originality Score displayed (if available)
   - AI Generated Probability displayed
   - Warning messages shown in yellow alert box
   - Score color-coded (green for >= 60, red for < 60)

3. **Timeline:**
   - Both Public and Private outputs display correctly
   - Private outputs show lock icon

---

## Performance Considerations

### Expected API Call Times

- **Embeddings Generation:** ~200-500ms
- **Similarity Search (pgvector):** ~50-200ms
- **Web Search (Google):** ~500-1500ms
- **LLM Originality Judgment (GPT-4):** ~2-5 seconds

**Total:** Approximately **3-7 seconds** per output creation

### Cost Estimates (per 1000 outputs)

- **Embeddings:** ~$0.004 (negligible)
- **GPT-4o Judgment:** ~$0.70
- **Google Custom Search:** ~$5 (if exceeding free tier)

**Total:** ~$5.70 per 1000 outputs

---

## Troubleshooting

### Issue: "OPENAI_API_KEY not set" Warning

**Solution:**
- Add `OPENAI_API_KEY=sk-...` to `.env` file
- Restart backend: `docker-compose restart backend`

### Issue: "SERPER_API_KEY not set" Warning

**Solution:**
- Sign up at https://serper.dev/ and get API key
- Add `SERPER_API_KEY=your_key_here` to `.env` file
- Restart backend: `docker-compose restart backend`

### Issue: Embedding Dimensions Error

**Symptom:** "Unexpected embedding dimensions: XXX (expected 1536)"

**Solution:**
- Verify you're using `text-embedding-3-small` model (not ada-002)
- Check OpenAI API response

### Issue: Similarity Search Not Working

**Symptom:** No similar outputs detected even for identical content

**Solution:**
1. Verify pgvector extension is enabled:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```
2. Verify HNSW index exists:
   ```sql
   SELECT * FROM pg_indexes WHERE indexname = 'idx_outputs_content_embedding_hnsw';
   ```
3. Re-run migrations if needed:
   ```bash
   poetry run alembic upgrade head
   ```

### Issue: Web Search Returns No Results

**Possible Causes:**
- Quota exceeded (2,500 free queries/month for Serper API)
- API key invalid
- Network connectivity issues

**Solution:**
- Check Serper.dev dashboard for remaining quota
- Verify `SERPER_API_KEY` in `.env`
- Check backend logs for HTTP errors

---

## Next Steps

After successful testing:

1. **Tune Thresholds:**
   - Adjust `ORIGINALITY_THRESHOLD` (default: 60)
   - Adjust `SIMILARITY_THRESHOLD` (default: 0.85)
   - Based on user feedback and false positive/negative rates

2. **Monitor Performance:**
   - Track API response times
   - Monitor costs
   - Implement caching if needed (Redis for embeddings)

3. **Phase 2 Features:**
   - User peer review (査読2)
   - Appeal mechanism for rejected content
   - Reverse simulation check (GPT predicts continuation)

4. **Feedback Loop:**
   - Collect user reports on false positives
   - Improve LLM prompt based on edge cases
   - A/B test threshold values

---

## Support

For issues or questions, refer to:
- [Implementation Design Doc](docs/design/originality-check-implementation.md)
- [Lighthouse Protocol](docs/the_lighthouse_protocol.md)
- Backend logs: `docker-compose logs -f backend`
