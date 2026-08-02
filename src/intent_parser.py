"""
Intent parser: natural-language query -> structured user_prefs dict.

The rest of the pipeline expects the same dict shape score_song() has always consumed:
    {favorite_genre, favorite_mood, target_energy, likes_acoustic}

We ask Gemini to extract these fields from a free-text request. If Gemini returns unusable output or is offline, 
we fall back to keyword matching so the pipeline still runs. Both paths are documented in the model card.
"""
import json
import re
from typing import Optional
from src.llm_client import generate

VALID_GENRES = {
    "pop", "lofi", "rock", "jazz", "hip-hop", "indie", "indie pop",
    "acoustic", "folk", "r&b", "classical", "electronic", "punk",
    "tango", "synthwave", "ambient",
}
VALID_MOODS = {
    "happy", "sad", "chill", "intense", "angry", "melancholy",
    "hopeful", "nostalgic", "moody", "focused", "relaxed",
}

PARSER_PROMPT = """You are a music-request parser. Convert the user's
free-text request into a JSON object with these fields ONLY:
- favorite_genre: one of {genres}, or null if not implied
- favorite_mood: one of {moods}, or null if not implied
- target_energy: a float between 0.0 (very calm) and 1.0 (very intense)
- likes_acoustic: true, false, or null if not implied

Respond with ONLY the JSON. No prose, no code fences.

User request: {query}
"""


def parse_query(query: str) -> tuple[dict, str]:
    """
    Parse a natural-language music request into a user_prefs dict.

    Returns:
        (user_prefs, source) where source is "gemini", "gemini-partial",
        or "keyword-fallback".
    """
    prompt = PARSER_PROMPT.format(
        genres=sorted(VALID_GENRES),
        moods=sorted(VALID_MOODS),
        query=query,
    )
    text, llm_source = generate(prompt)

    if llm_source == "offline":
        return _keyword_fallback(query), "keyword-fallback"

    parsed = _extract_json(text)
    if parsed is None:
        return _keyword_fallback(query), "keyword-fallback"

    cleaned = _validate_and_clean(parsed)
    if cleaned["target_energy"] is None:
        return _keyword_fallback(query), "gemini-partial"

    return cleaned, "gemini"


def _extract_json(text: str) -> Optional[dict]:
    """Pull the first JSON object out of an LLM response, tolerating stray text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _validate_and_clean(parsed: dict) -> dict:
    """Coerce parsed JSON into a valid user_prefs dict with safe defaults."""
    genre = parsed.get("favorite_genre")
    if genre is not None and str(genre).lower() not in VALID_GENRES:
        genre = None

    mood = parsed.get("favorite_mood")
    if mood is not None and str(mood).lower() not in VALID_MOODS:
        mood = None

    energy = parsed.get("target_energy")
    try:
        energy = float(energy) if energy is not None else None
        if energy is not None:
            energy = max(0.0, min(1.0, energy))
    except (TypeError, ValueError):
        energy = None

    acoustic = parsed.get("likes_acoustic")
    if isinstance(acoustic, str):
        acoustic = acoustic.lower() in ("true", "yes", "1")
    elif acoustic is not None:
        acoustic = bool(acoustic)

    return {
        "favorite_genre": genre.lower() if genre else None,
        "favorite_mood": mood.lower() if mood else None,
        "target_energy": energy if energy is not None else 0.5,
        "likes_acoustic": acoustic if acoustic is not None else False,
    }


def _keyword_fallback(query: str) -> dict:
    """
    Simple keyword-based parser used when the LLM is unavailable or returns junk.
    Not clever, but deterministic and always available.
    """
    q = query.lower()

    genre = next((g for g in VALID_GENRES if g in q), None)
    mood = next((m for m in VALID_MOODS if m in q), None)

    if any(w in q for w in ("calm", "quiet", "mellow", "soft", "slow")):
        energy = 0.25
    elif any(w in q for w in ("intense", "loud", "high energy", "energetic", "fast")):
        energy = 0.85
    else:
        energy = 0.5

    likes_acoustic = any(w in q for w in ("acoustic", "unplugged", "quiet"))

    return {
        "favorite_genre": genre,
        "favorite_mood": mood,
        "target_energy": energy,
        "likes_acoustic": likes_acoustic,
    }


if __name__ == "__main__":
    tests = [
        "Something melancholy and acoustic for a rainy night",
        "I want intense hip-hop for the gym",
        "Happy pop, high energy",
        "Give me a chill lofi vibe",
    ]
    for q in tests:
        prefs, source = parse_query(q)
        print(f"\nQuery: {q}")
        print(f"Source: {source}")
        print(f"Parsed: {prefs}")