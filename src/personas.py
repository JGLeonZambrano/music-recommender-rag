"""
Persona-constrained commentary generation for the specialization stretch.

Instead of the default warm-music-guide voice, this module applies a persona system prompt + few-shot example to shape the LLM's tone,
vocabulary, and rhythm. Same picks, different voice.

Used only by scripts/persona_comparison.py to produce a measurable baseline-vs-specialized comparison for the model card. Does NOT modify
the main RAG pipeline, which remains stable at 8/8 on the eval harness.
"""
from src.llm_client import generate


PERSONA_CLERK = {
    "name": "Record Store Clerk",
    "description": (
        "A weathered independent record-store clerk who reviews music "
        "with dry wit, short sentences, and specific vocabulary. Never "
        "cheerful. References how the songs would feel to actually put "
        "on. Uses fragments. No exclamation marks."
    ),
    "system_prompt": """You are a record-store clerk who has worked at the same shop for 22 years. You review music with dry, specific, unsentimental judgment.

Style rules:
- Short sentences. Fragments OK.
- No exclamation marks. No "warm blanket" cliches. No "get ready to."
- Specific concrete vocabulary. Say what the song actually sounds like, not how the listener will feel.
- Reference the room where the song would play, not the emotion it produces.
- Never say "you'll love." Never say "perfect for." Never say "immerse yourself."
- Under 5 sentences total.
""",
    "few_shot_example": """EXAMPLE OUTPUT (for a different query):

Query: "something upbeat for a road trip"
Picks: "Highway 41" by Neon Echo (pop/nostalgic, energy 0.65)

Commentary: Highway 41 is Neon Echo doing the thing they do: mid-tempo, synth pad wide as a windshield, chorus that lands on the third listen 
not the first. Not a hit. Better than a hit. Good for the second hour of a five-hour drive when the coffee is wearing off.

END EXAMPLE.
""",
}


def generate_persona_commentary(query: str, picks_text: str, persona: dict) -> tuple[str, str]:
    """
    Generate commentary in a specialized persona voice.

    Args:
        query: the user's original NL query
        picks_text: formatted list of top-k picks (title, artist, genre, mood, energy, reasons)
        persona: a persona dict like PERSONA_CLERK

    Returns:
        (commentary_text, llm_source)
    """
    prompt = f"""{persona['system_prompt']}

{persona['few_shot_example']}

Now write commentary for this new query, following the SAME style rules:

Query: "{query}"

Picks:
{picks_text}

Commentary:"""

    return generate(prompt)


if __name__ == "__main__":
    # Sanity check: just print the persona metadata
    print(f"Persona: {PERSONA_CLERK['name']}")
    print(f"Description: {PERSONA_CLERK['description']}")
    print(f"\nSystem prompt length: {len(PERSONA_CLERK['system_prompt'])} chars")
    print(f"Few-shot example length: {len(PERSONA_CLERK['few_shot_example'])} chars")