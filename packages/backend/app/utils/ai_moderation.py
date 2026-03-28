"""AI moderation utilities using OpenAI Moderation API with category-aware policies."""

import json
import re
from openai import AsyncOpenAI, OpenAI
from app.config import settings


# Category-based moderation policies
STRICT_CATEGORIES = {"SCIENCE", "TECHNOLOGY"}  # Descriptions also blocked
EXPRESSIVE_CATEGORIES = {"ART", "ESSAY", "DISCUSSION", "EDUCATION"}  # Only incitement blocked


class FlaggedSegment:
    """Represents a flagged segment of content."""

    def __init__(self, text: str, categories: list[str], start: int, end: int):
        self.text = text
        self.categories = categories
        self.start = start  # Character position in original text
        self.end = end


class ModerationResult:
    """Result from AI moderation check."""

    def __init__(
        self,
        is_safe: bool,
        flagged_categories: list[str] | None = None,
        flagged_segments: list[FlaggedSegment] | None = None,
        novelty_score: float | None = None,
    ):
        self.is_safe = is_safe
        self.flagged_categories = flagged_categories or []
        self.flagged_segments = flagged_segments or []
        self.novelty_score = novelty_score

    def get_user_feedback(self) -> str:
        """
        Generate user-friendly feedback message in Japanese.

        Returns:
            Feedback message explaining why content was rejected
        """
        if self.is_safe:
            return ""

        # Map OpenAI moderation categories to Japanese explanations
        category_messages = {
            "hate": "ヘイトスピーチや差別的な内容",
            "hate/threatening": "脅迫的なヘイトスピーチ",
            "harassment": "嫌がらせやいじめに該当する内容",
            "harassment/threatening": "脅迫的な嫌がらせ",
            "self-harm": "自傷行為を助長する内容",
            "self-harm/intent": "自傷行為の意図",
            "self-harm/instructions": "自傷行為の手順",
            "sexual": "性的に露骨な内容",
            "sexual/minors": "未成年者に関する性的な内容",
            "violence": "暴力的な内容",
            "violence/graphic": "過度にグラフィックな暴力描写",
        }

        feedback_parts = ["この投稿は以下の理由により承認できませんでした:"]

        # Add flagged segments with context
        if self.flagged_segments:
            feedback_parts.append("\n【問題のある箇所】")
            for i, segment in enumerate(self.flagged_segments[:3], 1):  # Show max 3 segments
                # Get category names
                cat_names = [
                    category_messages.get(cat, cat) for cat in segment.categories
                ]
                # Truncate text if too long
                display_text = (
                    segment.text[:100] + "..." if len(segment.text) > 100 else segment.text
                )
                feedback_parts.append(
                    f"{i}. 「{display_text}」\n   → {', '.join(cat_names)}が含まれています"
                )
        else:
            # Fallback to category-only feedback
            for cat in self.flagged_categories:
                msg = category_messages.get(cat, f"{cat}に該当する内容")
                feedback_parts.append(f"• {msg}が含まれています")

        return "\n".join(feedback_parts)


async def check_context_and_intent(
    content: str, flagged_categories: list[str]
) -> tuple[bool, str]:
    """
    Use LLM to distinguish between artistic description and incitement/advocacy.

    This function analyzes flagged content to determine if it:
    - Describes a situation (allowed in artistic works)
    - Advocates or incites harmful actions (always blocked)

    Args:
        content: The flagged content segment
        flagged_categories: Categories flagged by OpenAI Moderation API

    Returns:
        Tuple of (is_incitement, reasoning)
        - is_incitement: True if content advocates/incites harm
        - reasoning: Japanese explanation of the judgment
    """
    if not settings.OPENAI_API_KEY:
        return False, "APIキーが設定されていないため、スキップしました"

    prompt = f"""以下のテキストを分析し、「状況の描写」か「有害行為の推奨・扇動」かを判定してください。

**判定基準:**

✅ **許可（状況の描写）:**
- 小説・エッセイ・芸術作品における情景描写
- 歴史的事実や社会問題の客観的記述
- 登場人物の行動や心理の描写
- 例: 「母親が子どもを叩いた」「戦場で銃撃戦が起きた」

❌ **禁止（推奨・扇動）:**
- 特定の有害行為を「すべき」「やろう」と推奨
- 暴力・自傷・犯罪を肯定的に扇動
- 例: 「子どもを叩くべきだ」「◯◯を攻撃しよう」

**検出されたカテゴリ:** {', '.join(flagged_categories)}

**分析対象テキスト:**
---
{content}
---

**回答形式（JSON）:**
{{
  "is_incitement": true/false,
  "reasoning": "判定理由（日本語、200文字以内）"
}}"""

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-5.4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは表現の自由と公共の安全のバランスを判断する専門家です。芸術作品の描写と有害行為の推奨・扇動を区別してください。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_completion_tokens=300,
            response_format={"type": "json_object"},
        )

        result_text = response.choices[0].message.content
        if not result_text:
            return False, "LLM応答なし"

        result_data = json.loads(result_text)
        return result_data.get("is_incitement", False), result_data.get(
            "reasoning", ""
        )

    except Exception as e:
        print(f"⚠️ Context analysis error: {e}")
        # Default to safe (allow) on error
        return False, f"分析エラー: {e}"


async def check_content_safety(content: str, category: str = "ART") -> ModerationResult:
    """
    Check if content is safe using category-aware moderation.

    **Category-based policies:**
    - SCIENCE/TECHNOLOGY: Strict (descriptions also blocked)
    - ART/ESSAY/DISCUSSION/EDUCATION: Expressive (only incitement blocked)

    Performs multi-stage checking:
    1. Check entire content with OpenAI Moderation API
    2. If flagged, identify specific problematic segments
    3. For expressive categories: Use LLM to distinguish description vs incitement

    Args:
        content: The content to check
        category: Content category (default: "ART")

    Returns:
        ModerationResult with safety information and flagged segments
    """
    # If no API key is set, skip moderation (for development)
    if not settings.OPENAI_API_KEY:
        return ModerationResult(is_safe=True)

    category_upper = category.upper()
    is_strict_category = category_upper in STRICT_CATEGORIES
    is_expressive_category = category_upper in EXPRESSIVE_CATEGORIES

    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Stage 1: Check entire content
        response = await client.moderations.create(input=content)
        result = response.results[0]

        # If content is safe, return early
        if not result.flagged:
            return ModerationResult(is_safe=True)

        # Stage 2: Identify specific problematic segments
        flagged_categories = [
            cat
            for cat, flagged in result.categories.model_dump().items()
            if flagged
        ]

        # Level 1: Always block (all categories)
        critical_categories = {"sexual/minors", "self-harm/instructions"}
        if any(cat in critical_categories for cat in flagged_categories):
            print(f"🚨 [Level 1 Block] Critical violation: {flagged_categories}")
            flagged_segments = await _identify_flagged_segments(client, content)
            return ModerationResult(
                is_safe=False,
                flagged_categories=flagged_categories,
                flagged_segments=flagged_segments,
            )

        # Level 2: Category-dependent moderation
        # For strict categories (SCIENCE/TECH), block all flagged content
        if is_strict_category:
            print(f"🚨 [Level 2 Block - Strict Category] {category}: {flagged_categories}")
            flagged_segments = await _identify_flagged_segments(client, content)
            return ModerationResult(
                is_safe=False,
                flagged_categories=flagged_categories,
                flagged_segments=flagged_segments,
            )

        # For expressive categories (ART/ESSAY/etc), check if it's incitement
        if is_expressive_category:
            print(f"🔍 [Level 3 Check - Expressive Category] {category}: Analyzing context...")

            # Check if flagged content is incitement or just description
            is_incitement, reasoning = await check_context_and_intent(
                content, flagged_categories
            )

            if is_incitement:
                print(f"🚨 [Level 3 Block] Incitement detected: {reasoning}")
                flagged_segments = await _identify_flagged_segments(client, content)
                return ModerationResult(
                    is_safe=False,
                    flagged_categories=flagged_categories,
                    flagged_segments=flagged_segments,
                )
            else:
                print(f"✅ [Level 3 Allow] Artistic description: {reasoning}")
                # Allow content (it's artistic description, not incitement)
                return ModerationResult(is_safe=True)

        # Unknown category: default to strict
        print(f"⚠️ Unknown category '{category}', applying strict moderation")
        flagged_segments = await _identify_flagged_segments(client, content)
        return ModerationResult(
            is_safe=False,
            flagged_categories=flagged_categories,
            flagged_segments=flagged_segments,
        )

    except Exception as e:
        # Log the error in production
        print(f"⚠️ Moderation API error: {e}")
        # Default to safe if API fails
        return ModerationResult(is_safe=True)


async def _identify_flagged_segments(
    client: AsyncOpenAI, content: str
) -> list[FlaggedSegment]:
    """
    Identify specific segments of content that are flagged.

    Splits content by paragraphs and checks each one.

    Args:
        client: OpenAI client
        content: Full content text

    Returns:
        List of FlaggedSegment objects
    """
    flagged_segments = []

    # Split content into paragraphs (by double newline or single newline)
    paragraphs = re.split(r'\n\n+|\n', content)

    current_pos = 0

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        # Skip empty paragraphs
        if not paragraph or len(paragraph) < 10:
            current_pos += len(paragraph) + 1
            continue

        try:
            # Check this paragraph
            response = await client.moderations.create(input=paragraph)
            result = response.results[0]

            if result.flagged:
                # Collect flagged categories for this paragraph
                categories = [
                    category
                    for category, flagged in result.categories.model_dump().items()
                    if flagged
                ]

                # Find position in original content
                start = content.find(paragraph, current_pos)
                end = start + len(paragraph) if start != -1 else current_pos + len(paragraph)

                flagged_segments.append(
                    FlaggedSegment(
                        text=paragraph,
                        categories=categories,
                        start=start,
                        end=end,
                    )
                )

        except Exception as e:
            print(f"Error checking paragraph: {e}")
            # Continue checking other paragraphs

        current_pos += len(paragraph) + 1

    return flagged_segments


async def calculate_novelty_score(
    content: str, existing_outputs: list[str] | None = None
) -> float:
    """
    Calculate novelty score for content.

    This is a placeholder for Phase 2 implementation.
    In Phase 2, this will use OpenAI Embeddings + vector similarity search.

    Args:
        content: The content to score
        existing_outputs: Optional list of existing content to compare against

    Returns:
        Novelty score between 0.0 and 1.0
    """
    # Phase 1: Simple placeholder - return high novelty for all content
    # Phase 2: Will use embeddings + Pinecone/Weaviate for similarity search

    # For now, basic heuristic:
    # - Very short content (< 50 chars) gets lower score
    # - Longer, more detailed content gets higher score

    content_length = len(content)

    if content_length < 50:
        return 0.3
    elif content_length < 200:
        return 0.6
    elif content_length < 500:
        return 0.8
    else:
        return 0.9


async def determine_visibility(novelty_score: float, threshold: float = 0.5) -> str:
    """
    Determine if output should be public or private based on novelty score.

    Args:
        novelty_score: The calculated novelty score (0.0 to 1.0)
        threshold: Minimum score required for public visibility

    Returns:
        "public" or "private"
    """
    return "public" if novelty_score >= threshold else "private"
