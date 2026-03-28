"""
Originality check using GPT-4 for comprehensive content analysis.

This module implements the Lighthouse Protocol's philosophy:
LLM as a "sensor to detect divergence from average" rather than
"a device to produce average answers."
"""

import json
from typing import Optional

import openai
from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import settings


class StructuralElements(BaseModel):
    """Structural elements extracted from content for deep similarity analysis."""

    plot_structure: str = Field(
        ...,
        description="Narrative arc and key plot points (beginning, development, climax, resolution)",
    )

    character_roles: str = Field(
        ...,
        description="Main characters and their roles/relationships (protagonist, antagonist, supporting characters)",
    )

    themes: str = Field(
        ...,
        description="Core themes, messages, and philosophical ideas",
    )

    setting: str = Field(
        ...,
        description="Setting, world-building, time period, and atmosphere",
    )

    unique_elements: str = Field(
        ...,
        description="Unique elements that define this work (motifs, symbols, distinctive features)",
    )


class StructuralSimilarity(BaseModel):
    """Result of structural similarity comparison."""

    is_structurally_similar: bool = Field(
        ...,
        description="Whether content is structurally similar to existing works",
    )

    structural_similarity_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Structural similarity score (0-100, higher = more similar)",
    )

    similar_works: list[str] = Field(
        default_factory=list,
        description="List of similar works found (titles/descriptions)",
    )

    reasoning: str = Field(
        ...,
        description="Explanation of structural similarity in Japanese",
    )


class OriginalityJudgment(BaseModel):
    """Result of LLM-based originality judgment."""

    ai_generated_probability: int = Field(
        ...,
        ge=0,
        le=100,
        description="Probability that content is AI-generated (0-100%)",
    )

    existing_work_probability: int = Field(
        ...,
        ge=0,
        le=100,
        description="Probability that content is from existing published work (0-100%)",
    )

    suspected_source: Optional[str] = Field(
        None,
        description="Suspected source work (title, author) if detected, or null",
    )

    originality_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Originality score based on divergence and information density (0-100)",
    )

    reasoning: str = Field(
        ...,
        description="Brief explanation of the judgment in Japanese",
    )

    structural_similarity: Optional[StructuralSimilarity] = Field(
        None,
        description="Structural similarity analysis (if performed)",
    )


async def extract_structural_elements(content: str) -> Optional[StructuralElements]:
    """
    Stage 1: Extract structural elements from content for deep similarity analysis.

    This function analyzes the content to extract:
    - Plot structure (narrative arc, key events)
    - Character roles and relationships
    - Core themes and messages
    - Setting and world-building
    - Unique defining elements

    Args:
        content: Text content to analyze

    Returns:
        StructuralElements object, or None on error
    """
    if not settings.OPENAI_API_KEY:
        print("⚠️ OPENAI_API_KEY not set - skipping structural extraction")
        return None

    prompt = f"""以下のコンテンツを分析し、著作権侵害判定で使われるような**構造的要素**を抽出してください。

表面的な文章の一致度ではなく、作品の本質を構成する要素を分析します:

1. **プロット構造 (plot_structure)**
   - 物語の展開（起承転結、ストーリーライン）
   - 主要な出来事やターニングポイント
   - 論理展開の構造

2. **登場人物の役割 (character_roles)**
   - 主要な登場人物とその役割
   - 人物間の関係性や力学
   - キャラクターの特徴や動機

3. **テーマ (themes)**
   - 中心的なテーマやメッセージ
   - 哲学的・思想的な要素
   - 作品が伝えようとする価値観

4. **舞台設定 (setting)**
   - 時代背景、場所、世界観
   - 雰囲気や世界観の特徴
   - 環境が物語に与える影響

5. **独自要素 (unique_elements)**
   - この作品を特徴づける独特の要素
   - 象徴、モチーフ、繰り返されるパターン
   - 他作品と区別できる特徴

**重要**:
- エッセイや体験談の場合も、論理構造や主張の展開パターンを分析
- 技術的な記事の場合は、説明の順序や論理構造を抽出
- 短文の場合は「該当なし」または簡潔に記述

**分析対象コンテンツ:**
---
{content}
---

**回答形式（JSON）:**
{{
  "plot_structure": "プロット構造の説明（200文字以内）",
  "character_roles": "登場人物の役割（200文字以内）",
  "themes": "テーマとメッセージ（200文字以内）",
  "setting": "舞台設定（200文字以内）",
  "unique_elements": "独自要素（200文字以内）"
}}"""

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-5.4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは著作権侵害判定の専門家です。表面的な文章一致ではなく、作品の構造・概念・登場人物の特徴など、本質的な要素を分析してください。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_completion_tokens=800,
            response_format={"type": "json_object"},
        )

        result_text = response.choices[0].message.content

        if not result_text:
            print("⚠️ Empty response from GPT-4 structural extraction")
            return None

        # Parse JSON response
        result_data = json.loads(result_text)

        # Validate and create StructuralElements
        elements = StructuralElements(**result_data)

        print(f"📊 [Stage 1] 構造要素抽出完了:")
        print(f"   - プロット: {elements.plot_structure[:60]}...")
        print(f"   - 登場人物: {elements.character_roles[:60]}...")
        print(f"   - テーマ: {elements.themes[:60]}...")

        return elements

    except openai.APIError as e:
        print(f"⚠️ OpenAI API error during structural extraction: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse GPT-4 response as JSON: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Unexpected error during structural extraction: {e}")
        return None


async def compare_structural_similarity(
    target_elements: StructuralElements,
    similar_outputs: Optional[list] = None,
    web_search_results: Optional[list] = None,
) -> Optional[StructuralSimilarity]:
    """
    Stage 2: Compare structural elements with existing content.

    This function performs deep structural similarity analysis:
    - Compares plot structures and narrative arcs
    - Compares character roles and relationships
    - Compares themes and messages
    - Identifies structural plagiarism beyond surface-level text matching

    Args:
        target_elements: Structural elements extracted from target content
        similar_outputs: Optional list of similar outputs from database
        web_search_results: Optional list of web search results

    Returns:
        StructuralSimilarity object, or None on error
    """
    if not settings.OPENAI_API_KEY:
        print("⚠️ OPENAI_API_KEY not set - skipping structural comparison")
        return None

    # Build comparison context
    comparison_context = ""

    if similar_outputs:
        comparison_context += "\n\n【プラットフォーム内の類似投稿】\n"
        for i, sim_output in enumerate(similar_outputs[:3], 1):
            similarity_pct = int(sim_output.similarity * 100)
            preview = sim_output.output.content[:200] + "..." if len(sim_output.output.content) > 200 else sim_output.output.content
            comparison_context += f"\n{i}. 類似度{similarity_pct}% - 投稿内容:\n{preview}\n"

    if web_search_results:
        comparison_context += "\n\n【Web検索結果】\n"
        for i, result in enumerate(web_search_results[:3], 1):
            comparison_context += f"\n{i}. {result.title}\n   URL: {result.link}\n   内容: {result.snippet}\n"

    if not comparison_context:
        # No similar content to compare with
        return StructuralSimilarity(
            is_structurally_similar=False,
            structural_similarity_score=0,
            similar_works=[],
            reasoning="比較対象となる類似コンテンツが見つかりませんでした",
        )

    prompt = f"""以下の**対象コンテンツの構造要素**と**既存コンテンツ**を比較し、構造的類似性を評価してください。

著作権侵害判定で重視される以下の観点から分析:

1. **プロット構造の類似性**
   - ストーリー展開や論理展開のパターンが似ているか
   - 主要な転換点や結論が類似しているか

2. **登場人物の類似性**
   - キャラクターの役割や関係性が似ているか
   - 性格特性や動機が類似しているか

3. **テーマの類似性**
   - 中心的なメッセージや哲学が似ているか
   - 価値観や主張の方向性が一致しているか

4. **独自要素の重複**
   - 特徴的なモチーフや象徴が共通しているか
   - 表現手法や文体の構造が類似しているか

**重要な判定基準:**
- **表面的な言い回しの違いは無視**し、本質的な構造の一致を重視
- 複数の要素（プロット+登場人物+テーマ）が同時に類似している場合は高リスク
- 一般的なテーマ（例: 愛、成長、正義）だけの一致は低リスク
- 具体的なストーリー展開の一致は高リスク

**対象コンテンツの構造要素:**
- プロット: {target_elements.plot_structure}
- 登場人物: {target_elements.character_roles}
- テーマ: {target_elements.themes}
- 舞台設定: {target_elements.setting}
- 独自要素: {target_elements.unique_elements}
{comparison_context}

**回答形式（JSON）:**
{{
  "is_structurally_similar": true/false,
  "structural_similarity_score": 0-100の整数（0=全く異なる、100=構造的にほぼ同一）,
  "similar_works": ["類似作品1", "類似作品2"...] または [],
  "reasoning": "構造的類似性の判定理由（日本語、300文字以内）"
}}

**スコアリング基準:**
- 80-100: 複数の構造要素がほぼ一致（著作権侵害の可能性大）
- 60-79: 明確な構造的類似性あり（要注意）
- 40-59: 部分的な類似性（一般的なパターンの範囲）
- 0-39: 構造的に異なる（独立した作品）"""

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-5.4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは著作権侵害判定の専門家です。表面的な文章一致ではなく、プロット構造・登場人物の役割・テーマ・独自要素などの構造的類似性を分析してください。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_completion_tokens=600,
            response_format={"type": "json_object"},
        )

        result_text = response.choices[0].message.content

        if not result_text:
            print("⚠️ Empty response from GPT-4 structural comparison")
            return None

        # Parse JSON response
        result_data = json.loads(result_text)

        # Validate and create StructuralSimilarity
        similarity = StructuralSimilarity(**result_data)

        print(f"📊 [Stage 2] 構造的類似性分析完了:")
        print(f"   - 類似判定: {'はい' if similarity.is_structurally_similar else 'いいえ'}")
        print(f"   - 類似スコア: {similarity.structural_similarity_score}/100")
        if similarity.similar_works:
            print(f"   - 類似作品: {', '.join(similarity.similar_works[:3])}")

        return similarity

    except openai.APIError as e:
        print(f"⚠️ OpenAI API error during structural comparison: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse GPT-4 response as JSON: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Unexpected error during structural comparison: {e}")
        return None


async def check_originality_with_llm(
    content: str,
    similar_outputs: Optional[list] = None,
    web_search_results: Optional[list] = None,
) -> Optional[OriginalityJudgment]:
    """
    Perform comprehensive originality check using GPT-4 with 2-stage structural analysis.

    **2-Stage Workflow:**
    Stage 1: Extract structural elements (plot, characters, themes, setting)
    Stage 2: Compare structural similarity with existing content
    Stage 3: Final originality judgment considering structural analysis

    This function evaluates content across multiple dimensions:
    1. AI generation probability (detecting LLM-typical patterns)
    2. Existing work detection (identifying known literature, articles, etc.)
    3. Structural similarity (plot, characters, themes - like copyright analysis)
    4. Originality score (based on Lighthouse Protocol principles)

    The originality score evaluates:
    - Divergence: How far the content deviates from typical web data/AI responses
    - Density: Concentration of first-hand information (5W1H, detailed observations)
    - Unique perspective: Human-specific obsessions, logical leaps
    - Structural uniqueness: Original plot/concept/character structures

    Args:
        content: Text content to analyze
        similar_outputs: Optional list of similar outputs from internal database
        web_search_results: Optional list of web search results for context

    Returns:
        OriginalityJudgment object with structural_similarity field, or None on error

    Scoring philosophy (Lighthouse Protocol):
    - High score (80-100): Strong divergence + high information density
    - Medium score (60-79): Moderate originality, some unique insights
    - Low score (30-59): Typical/derivative, low first-hand information
    - Very low (0-29): AI-generated generic content or known plagiarism
    """
    if not settings.OPENAI_API_KEY:
        print("⚠️ OPENAI_API_KEY not set - skipping LLM originality check")
        return None

    print("🔍 [Originality Check] Starting 2-stage structural analysis...")

    # ============================================
    # Stage 1: Extract structural elements
    # ============================================
    structural_elements = await extract_structural_elements(content)

    if not structural_elements:
        print("⚠️ Structural extraction failed, proceeding without structural analysis")

    # ============================================
    # Stage 2: Compare structural similarity
    # ============================================
    structural_similarity = None
    if structural_elements and (similar_outputs or web_search_results):
        structural_similarity = await compare_structural_similarity(
            target_elements=structural_elements,
            similar_outputs=similar_outputs,
            web_search_results=web_search_results,
        )

        if not structural_similarity:
            print("⚠️ Structural comparison failed, proceeding without it")

    # ============================================
    # Build context for final judgment
    # ============================================

    # Add structural similarity context
    structural_context = ""
    if structural_similarity:
        structural_context = f"\n\n【🔍 構造的類似性分析結果（Stage 2）】\n"
        structural_context += f"- 構造的類似判定: {'**類似あり**' if structural_similarity.is_structurally_similar else '類似なし'}\n"
        structural_context += f"- 構造類似スコア: **{structural_similarity.structural_similarity_score}/100**\n"

        if structural_similarity.similar_works:
            structural_context += f"- 類似作品: {', '.join(structural_similarity.similar_works)}\n"

        structural_context += f"- 分析: {structural_similarity.reasoning}\n"

        # Critical instruction if high structural similarity
        if structural_similarity.structural_similarity_score >= 70:
            structural_context += f"\n⚠️ **重要**: 構造類似スコア{structural_similarity.structural_similarity_score}点は著作権侵害レベルの類似性です。オリジナリティスコアは30点未満にすべきです。\n"

    # Build context from similar outputs (internal database)
    similarity_context = ""
    if similar_outputs:
        similarity_context = "\n\n【⚠️ プラットフォーム内の類似投稿】\n"
        for i, sim_output in enumerate(similar_outputs[:3], 1):
            similarity_pct = int(sim_output.similarity * 100)
            preview = sim_output.output.content[:100] + "..." if len(sim_output.output.content) > 100 else sim_output.output.content
            similarity_context += f"{i}. 類似度{similarity_pct}% - 「{preview}」\n"

        # Critical instruction if high similarity
        if similar_outputs and similar_outputs[0].similarity >= 0.85:
            similarity_context += f"\n⚠️ **重要**: 最高類似度{int(similar_outputs[0].similarity * 100)}%は極めて高く、ほぼ同一内容です。オリジナリティスコアは30点未満にすべきです。\n"

    # Build context from web search results
    web_context = ""
    if web_search_results:
        web_context = "\n\n【Web検索結果】\n"
        web_context += "⚠️ 注意: これらは部分一致の可能性があります。スニペット内容を慎重に確認し、本当に元コンテンツと関連があるか判断してください。\n\n"
        for i, result in enumerate(web_search_results[:3], 1):
            web_context += f"{i}. {result.title}\n   URL: {result.link}\n   スニペット: {result.snippet}\n"

        # Critical instruction if many results found
        if len(web_search_results) >= 5:
            web_context += f"\n⚠️ **重要**: Web上で{len(web_search_results)}件もの類似コンテンツが見つかりました。ただし、キーワードのみの一致ではなく、実際の内容が類似しているか確認してください。\n"

    # Construct prompt
    prompt = f"""以下のテキストを分析し、3つの観点から評価してください:

**【重要】構造的類似性分析が完了しています。この結果を必ず考慮してください。**{structural_context}

1. **AI生成確率（0-100%）**
   - ChatGPT/Claude等のLLM特有のパターン（定型表現、構造、語彙）を検出
   - 例: 「〜が重要です」「〜と言えるでしょう」等の典型的な締めくくり
   - 過度に整った構成、バランスの取れた視点の羅列

2. **既存著作物の可能性（0-100%）**
   - 既知の小説、論文、記事、ブログ等からの引用・盗用の可能性
   - 文体、内容、固有の表現から判断
   - **構造的類似性スコアが高い場合（70点以上）は、既存著作物の可能性も高く評価**
   - **⚠️ 重要**: Web検索結果は参考情報です。必ず以下を確認してください：
     - スニペット内容が実際に本文と一致しているか
     - 単なるキーワードの一致ではなく、実質的な内容の類似性があるか
     - 著者名・作品名は確実な証拠がある場合のみ提示（推測禁止）
   - 具体的な作品名・著者名が**明確に確認できる場合のみ**提示（不確実な場合はnull）

3. **オリジナリティスコア（0-100点）**
   以下の基準で評価:

   **A. 乖離度（Divergence）** - 平均からの距離
   - 一般的なWeb記事やAI回答と異なる視点・切り口があるか
   - 予測困難な論理展開、意外な結論があるか

   **B. 内部密度（Density）** - 一次情報の濃度
   - 5W1H（いつ、どこで、誰が、何を、なぜ、どのように）の具体性
   - 個人的体験、独自観察、微細な描写の量
   - 感情の矛盾や複雑さ（人間特有の揺らぎ）

   **C. 構造的独自性（NEW）**
   - **構造的類似性スコアが高い場合（70点以上）は、オリジナリティスコアを大幅減点（-30〜-50点）**
   - プロット、登場人物、テーマの組み合わせが既存作品と類似している場合は低評価

   **D. 独自性の本質**
   - AIであっても、独自の視点・洞察・論理展開があれば高評価
   - 人類の知に貢献する「新しい知見」があるか

   **スコアリング基準:**
   - 80-100点: 強い乖離 + 高密度な一次情報 + 構造的独自性 + 独自の論理展開
   - 60-79点: 中程度のオリジナリティ、独自の視点あり
   - 30-59点: 典型的・派生的、一次情報が少ない、または構造的類似性あり
   - 0-29点: AI生成的、既知の盗用、または構造的にほぼ同一{similarity_context}{web_context}

**分析対象テキスト:**
---
{content}
---

**回答形式（JSON）:**
{{
  "ai_generated_probability": 0-100の整数,
  "existing_work_probability": 0-100の整数,
  "suspected_source": "作品名・著者名 または null",
  "originality_score": 0-100の整数,
  "reasoning": "判定理由の簡潔な説明（日本語、200文字以内）"
}}"""

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-5.4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは文章の独自性を評価する専門家です。Lighthouse Protocolに基づき、LLMを「平均からの乖離を検知するセンサー」として活用し、コンテンツの真の独自性を評価してください。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_completion_tokens=500,
            response_format={"type": "json_object"},
        )

        result_text = response.choices[0].message.content

        if not result_text:
            print("⚠️ Empty response from GPT-4 originality check")
            return None

        # Parse JSON response
        result_data = json.loads(result_text)

        # Validate and create OriginalityJudgment
        judgment = OriginalityJudgment(**result_data)

        # Add structural similarity analysis result
        judgment.structural_similarity = structural_similarity

        print(f"✅ [Final Judgment] オリジナリティチェック完了:")
        print(f"   - AI生成確率: {judgment.ai_generated_probability}%")
        print(f"   - 既存著作物可能性: {judgment.existing_work_probability}%")
        print(f"   - オリジナリティスコア: {judgment.originality_score}/100")
        print(f"   - 判定理由: {judgment.reasoning}")
        if judgment.structural_similarity:
            print(f"   - 構造的類似性: {judgment.structural_similarity.structural_similarity_score}/100")

        return judgment

    except openai.APIError as e:
        print(f"⚠️ OpenAI API error during originality check: {e}")
        return None
    except openai.RateLimitError as e:
        print(f"⚠️ OpenAI rate limit exceeded during originality check: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse GPT-4 response as JSON: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Unexpected error during originality check: {e}")
        return None


def generate_originality_warnings(
    judgment: OriginalityJudgment,
    similar_outputs: Optional[list] = None,
    web_results: Optional[list] = None,
) -> list[str]:
    """
    Generate user-friendly warning messages based on originality judgment.

    Args:
        judgment: OriginalityJudgment from LLM (includes structural_similarity)
        similar_outputs: Optional list of similar outputs found in database
        web_results: Optional list of web search results

    Returns:
        List of warning messages in Japanese
    """
    warnings = []

    # Check for structural similarity (NEW - highest priority)
    if judgment.structural_similarity:
        struct_sim = judgment.structural_similarity
        if struct_sim.is_structurally_similar and struct_sim.structural_similarity_score >= 70:
            warning_text = (
                f"🚨 構造的類似性警告: このコンテンツは既存作品と構造的に類似しています "
                f"（類似スコア{struct_sim.structural_similarity_score}/100）"
            )
            if struct_sim.similar_works:
                warning_text += f"\n   類似作品: {', '.join(struct_sim.similar_works[:3])}"
            warning_text += f"\n   分析: {struct_sim.reasoning}"
            warnings.append(warning_text)

    # Check for plagiarism from existing work
    if judgment.existing_work_probability > 70:
        if judgment.suspected_source:
            # Specific work identified
            warnings.append(
                f"⚠️ 既存著作物の可能性: この内容は「{judgment.suspected_source}」からの "
                f"引用・盗用の可能性があります（確率{judgment.existing_work_probability}%）"
            )
        else:
            # High probability but no specific source
            warnings.append(
                f"⚠️ 既存著作物の可能性: この内容は既存の著作物と類似している可能性があります "
                f"（確率{judgment.existing_work_probability}%）"
            )

    # Check for AI-generated low-originality content
    if judgment.ai_generated_probability > 80 and judgment.originality_score < 30:
        warnings.append(
            f"⚠️ AI生成コンテンツの可能性: この内容はAIによって生成された可能性が高く "
            f"（確率{judgment.ai_generated_probability}%）、独自性が不足しています "
            f"（スコア{judgment.originality_score}/100）"
        )

    # Check for low originality score (general warning)
    if judgment.originality_score < 60 and not warnings:
        # Add reasoning as warning if no other warnings exist
        warnings.append(
            f"⚠️ オリジナリティ不足: {judgment.reasoning}"
        )

    # Check for similar content in database
    if similar_outputs:
        for similar in similar_outputs:
            similarity_pct = int(similar.similarity * 100)
            warnings.append(
                f"⚠️ 類似投稿: 既存の投稿「{similar.output.content[:50]}...」と "
                f"{similarity_pct}%の類似度があります"
            )

    # Check for web matches with URLs
    if web_results and len(web_results) > 0:
        # Add summary warning
        warnings.append(
            f"⚠️ Web上の類似コンテンツ: {len(web_results)}件の類似する内容が "
            f"インターネット上で見つかりました"
        )

        # Add detailed URL references (show top 3)
        for i, result in enumerate(web_results[:3], 1):
            title = result.title if len(result.title) <= 50 else result.title[:50] + "..."
            warnings.append(
                f"   {i}. 「{title}」\n      URL: {result.link}"
            )

    return warnings


def should_approve_for_public(
    judgment: OriginalityJudgment,
    threshold: int = 60,
    similar_outputs: Optional[list] = None,
    web_results: Optional[list] = None,
) -> tuple[bool, str]:
    """
    Determine if content should be approved for public visibility.

    Based on Lighthouse Protocol: Only content passing 査読1 (LLM review)
    can proceed to become a public "work."

    **NEW**: Includes structural similarity check for copyright-level analysis.

    Args:
        judgment: OriginalityJudgment from LLM (includes structural_similarity)
        threshold: Minimum originality score for public (default 60)
        similar_outputs: Optional list of similar outputs from database
        web_results: Optional list of web search results

    Returns:
        Tuple of (approved, reason)
        - approved: True if content should be public
        - reason: Explanation message in Japanese
    """
    # CRITICAL: Reject if high structural similarity (NEW - highest priority)
    if judgment.structural_similarity:
        struct_sim = judgment.structural_similarity
        if struct_sim.is_structurally_similar and struct_sim.structural_similarity_score >= 70:
            similar_works_text = ""
            if struct_sim.similar_works:
                similar_works_text = f"（類似作品: {', '.join(struct_sim.similar_works[:2])}）"
            return False, f"構造的類似性スコア{struct_sim.structural_similarity_score}点で著作権侵害レベルの類似性が検出されました{similar_works_text}"

    # CRITICAL: Reject if high similarity with existing internal content
    if similar_outputs and similar_outputs[0].similarity >= 0.85:
        similarity_pct = int(similar_outputs[0].similarity * 100)
        return False, f"既存投稿と{similarity_pct}%の極めて高い類似度があり、重複コンテンツと判断されました"

    # CRITICAL: Reject if many web matches found (likely plagiarism)
    if web_results and len(web_results) >= 5:
        return False, f"Web上で{len(web_results)}件もの類似コンテンツが見つかり、既存著作物の可能性が高いため却下されました"

    # Reject if suspected plagiarism from LLM judgment
    if judgment.existing_work_probability > 70 and judgment.suspected_source:
        return False, f"既存著作物「{judgment.suspected_source}」からの盗用の疑いがあります"

    # Reject if AI-generated with low originality
    if judgment.ai_generated_probability > 80 and judgment.originality_score < 30:
        return False, "AI生成コンテンツで独自性が不足しています"

    # Check originality score threshold
    if judgment.originality_score < threshold:
        return (
            False,
            f"オリジナリティスコア{judgment.originality_score}点（基準{threshold}点未満）のため、"
            f"Private投稿として保存されます",
        )

    # Approved
    approval_message = f"査読1通過: オリジナリティスコア{judgment.originality_score}点で承認されました"
    if judgment.structural_similarity and judgment.structural_similarity.structural_similarity_score > 0:
        approval_message += f"（構造類似スコア: {judgment.structural_similarity.structural_similarity_score}点）"

    return (True, approval_message)
