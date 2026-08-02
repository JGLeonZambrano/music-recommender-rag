"""
Smoke test: does our Gemini API key authenticate and return a response?

Run: python scripts/verify_gemini.py

If this prints a short poem, the key works and Phase 1C can proceed.
If it prints an error, we fall back to the offline generator.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    sys.exit(1)

print(f"Key loaded (starts with: {api_key[:6]}..., length: {len(api_key)})")
print("Attempting Gemini call...\n")

try:
    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents="Write one line of poetry about music. Just the line, no preamble.",
    )
    print("SUCCESS. Gemini responded:")
    print(f"  {response.text.strip()}")
    print("\nKey is working. Phase 1C can use Gemini for the RAG generation step.")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
    print("\nWe'll use the offline generator for Phase 1C. This is fine.")
    sys.exit(2)