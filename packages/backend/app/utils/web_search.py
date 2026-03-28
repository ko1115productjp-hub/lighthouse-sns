"""Web search utility using Serper API for plagiarism detection."""

import re
import httpx
from typing import Optional

from app.config import settings


class WebSearchResult:
    """Result from web search."""

    def __init__(self, title: str, link: str, snippet: str):
        """
        Initialize web search result.

        Args:
            title: Page title
            link: URL of the page
            snippet: Text snippet showing the match
        """
        self.title = title
        self.link = link
        self.snippet = snippet


def extract_search_phrases(content: str, num_phrases: int = 3) -> list[str]:
    """
    Extract distinctive MULTI-SENTENCE phrases from content for web search.

    Uses consecutive sentences (2-3 sentences combined) to create longer,
    more distinctive search phrases. This reduces false positives from
    keyword-only matches.

    Args:
        content: Text content to analyze
        num_phrases: Number of phrases to extract (default 3)

    Returns:
        List of search phrases (each 60-150 chars, quoted for exact match)
    """
    if not content or len(content) < 50:
        return []

    phrases = []

    # Remove excessive whitespace
    content = re.sub(r"\s+", " ", content).strip()

    # Split into sentences (Japanese and English)
    sentences = re.split(r"[。！？.!?]+(?:\s|$)", content)
    sentences = [s.strip() for s in sentences if s.strip() and len(s) >= 15]

    if len(sentences) < 2:
        return []

    # Extract multi-sentence phrases
    step = max(1, len(sentences) // num_phrases)

    for i in range(0, len(sentences) - 1, step):
        # Combine 2-3 consecutive sentences
        combined = ""
        sentence_count = 0

        for j in range(i, min(i + 3, len(sentences))):
            if len(combined) + len(sentences[j]) > 150:
                break
            if combined:
                combined += "。"
            combined += sentences[j]
            sentence_count += 1

            # Accept if we have 60-150 chars and at least 2 sentences
            if len(combined) >= 60 and sentence_count >= 2:
                # Wrap in quotes for exact match search
                phrases.append(f'"{combined}"')
                break

        if len(phrases) >= num_phrases:
            break

    # Fallback: if no multi-sentence phrases found, use longer single sentences
    if not phrases:
        for sentence in sentences:
            if 50 <= len(sentence) <= 150:
                phrases.append(f'"{sentence}"')
                if len(phrases) >= num_phrases:
                    break

    return phrases


async def search_web_for_content(
    content: str,
    num_phrases: int = 3,
    results_per_phrase: int = 3,
) -> list[WebSearchResult]:
    """
    Search the web for potentially matching content using Serper API.

    Extracts distinctive phrases from the content and searches for them.
    Returns results that may indicate plagiarism or existing published work.

    Args:
        content: Text content to search for
        num_phrases: Number of search phrases to extract (default 3)
        results_per_phrase: Max results per phrase (default 3)

    Returns:
        List of WebSearchResult objects

    Note:
        Requires SERPER_API_KEY to be set in settings.
        Returns empty list if not configured.
    """
    if not settings.SERPER_API_KEY:
        print("⚠️ SERPER_API_KEY not set - skipping web search")
        return []

    # Extract search phrases
    phrases = extract_search_phrases(content, num_phrases=num_phrases)

    if not phrases:
        return []

    print(f"🔍 [Web Search] Extracted {len(phrases)} search phrases:")
    for i, phrase in enumerate(phrases, 1):
        print(f"   {i}. \"{phrase}\"")

    all_results = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for phrase in phrases:
                print(f"🌐 [Serper API] Searching for: \"{phrase[:50]}...\"" if len(phrase) > 50 else f"🌐 [Serper API] Searching for: \"{phrase}\"")
                try:
                    # Make request to Serper API
                    response = await client.post(
                        "https://google.serper.dev/search",
                        headers={
                            "X-API-KEY": settings.SERPER_API_KEY,
                            "Content-Type": "application/json",
                        },
                        json={
                            "q": phrase,
                            "gl": "jp",  # Geographic location: Japan
                            "hl": "ja",  # Language: Japanese
                            "num": results_per_phrase,  # Number of results
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()

                        # Parse organic results
                        if "organic" in data:
                            print(f"   ✅ Found {len(data['organic'])} results")

                            # Remove quotes from phrase for content matching
                            phrase_clean = phrase.strip('"')

                            # Extract a distinctive substring for matching (first 30 chars)
                            # This helps verify the result is actually relevant
                            match_substring = phrase_clean[:50] if len(phrase_clean) >= 50 else phrase_clean[:30]

                            for item in data["organic"][:results_per_phrase]:
                                snippet = item.get("snippet", "")
                                title = item.get("title", "")
                                link = item.get("link", "")

                                # CRITICAL: Verify the snippet actually contains part of our search phrase
                                # This prevents keyword-only matches (e.g., "東京" matching Wikipedia)
                                if match_substring not in snippet and match_substring not in title:
                                    print(f"      ❌ Filtered out (no phrase match): {title[:40]}...")
                                    continue

                                search_result = WebSearchResult(
                                    title=title,
                                    link=link,
                                    snippet=snippet,
                                )
                                print(f"      ✅ {search_result.title[:60]}...")
                                print(f"        URL: {search_result.link}")
                                print(f"        Snippet: {search_result.snippet[:100]}...")
                                all_results.append(search_result)
                        else:
                            print(f"   ⚠️ No organic results found")
                    else:
                        print(
                            f"⚠️ Serper API error for phrase '{phrase[:30]}...': "
                            f"Status {response.status_code}"
                        )

                except httpx.HTTPError as e:
                    print(f"⚠️ HTTP error during web search for phrase '{phrase[:30]}...': {e}")
                    continue

    except Exception as e:
        print(f"⚠️ Error during web search: {e}")
        return []

    # Remove duplicates based on URL
    seen_urls = set()
    unique_results = []

    for result in all_results:
        if result.link not in seen_urls:
            seen_urls.add(result.link)
            unique_results.append(result)

    return unique_results


async def check_plagiarism_from_web(content: str) -> tuple[bool, list[WebSearchResult]]:
    """
    Check if content appears to be plagiarized from web sources.

    This is a convenience function that performs web search and
    determines if matches found are likely plagiarism.

    Args:
        content: Text content to check

    Returns:
        Tuple of (is_likely_plagiarized, search_results)
        - is_likely_plagiarized: True if suspicious matches found
        - search_results: List of matching web pages
    """
    results = await search_web_for_content(content)

    # If we found results, consider it potentially plagiarized
    # (The LLM will make final judgment on whether it's actual plagiarism)
    is_suspicious = len(results) > 0

    return is_suspicious, results
