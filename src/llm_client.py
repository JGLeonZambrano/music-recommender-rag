"""
LLM client for the Music Recommender RAG system.

Wraps Gemini API calls behind a single generate() function so the rest of the codebase doesn't care which model or provider
is in use. If the API call fails (503, network, quota, etc.), generate() falls back to a deterministic offline template so 
the pipeline still runs end-to-end.

This "graceful degradation" is a required reliability behavior for Project 4 
(see rubric: Reliability, Evaluation, or Guardrail Component)
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Current GA model as of August 2026. Google retires model names every
# few months, so we keep this in one place for easy swapping.
MODEL_NAME = "gemini-3.6-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"

_client = None


def _get_client():
    """Lazy-initialize the Gemini client. Returns None if no key is set."""
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        _client = genai.Client(api_key=api_key)
        return _client
    except Exception as e:
        print(f"[llm_client] Failed to initialize Gemini client: {e}")
        return None


def generate(prompt: str, max_retries: int = 2) -> tuple[str, str]:
    """
    Send a prompt to Gemini and return (response_text, source).

    Args:
        prompt: The full prompt string to send.
        max_retries: How many times to retry the primary model on 503.

    Returns:
        (text, source) where source is one of:
          - "gemini-3.6-flash" (primary success)
          - "gemini-3.5-flash-lite" (fallback model success)
          - "offline" (both API paths failed, deterministic response used)
    """
    client = _get_client()
    if client is None:
        return _offline_response(prompt), "offline"

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            return response.text.strip(), MODEL_NAME
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "UNAVAILABLE" in error_str:
                if attempt < max_retries:
                    continue
                break
            print(f"[llm_client] {MODEL_NAME} failed: {type(e).__name__}")
            break

    try:
        response = client.models.generate_content(
            model=FALLBACK_MODEL,
            contents=prompt,
        )
        return response.text.strip(), FALLBACK_MODEL
    except Exception as e:
        print(f"[llm_client] Fallback model also failed: {type(e).__name__}")

    return _offline_response(prompt), "offline"


def _offline_response(prompt: str) -> str:
    """
    Deterministic response when no LLM is reachable. Keeps the pipeline
    functional and lets tests run without network access.
    """
    return (
        "[Offline mode] The LLM was unreachable. "
        "Falling back to structured recommendations without natural-language commentary."
    )


if __name__ == "__main__":
    text, source = generate("Say hello in one short sentence.")
    print(f"Source: {source}")
    print(f"Response: {text}")