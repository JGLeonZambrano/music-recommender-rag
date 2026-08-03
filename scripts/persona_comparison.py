"""
Baseline vs specialized commentary comparison.

Runs the same picks through two commentary generators:
  1. Baseline (current warm-music-guide voice from rag_pipeline.COMMENTARY_PROMPT)
  2. Specialized (PERSONA_CLERK from src/personas.py)

Prints both side by side and writes the comparison to assets/persona_comparison.txt for citation in the model card.

Rubric: Fine-Tuning or Specialization stretch (+2).
Constrained-tone/style approach, not weight fine-tuning.

Run:
    python scripts/persona_comparison.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.recommender import load_songs
from src.retriever import SongRetriever
from src.rag_pipeline import recommend, COMMENTARY_PROMPT
from src.personas import PERSONA_CLERK, generate_persona_commentary
from src.llm_client import generate


TEST_QUERIES = [
    "something melancholy and acoustic for a rainy night",
    "smoky jazz for a late dinner with friends",
    "80s throwback synthwave, driving at night",
]


def measure_difference(baseline: str, specialized: str) -> dict:
    """Simple measurable stylistic markers."""
    def count_exclamations(text): return text.count("!")
    def avg_sentence_len(text):
        sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        if not sentences:
            return 0
        return sum(len(s.split()) for s in sentences) / len(sentences)
    def count_forbidden_cliches(text):
        cliches = ["you'll love", "perfect for", "immerse", "warm blanket",
                   "get ready to", "settle in", "you're looking for"]
        return sum(1 for c in cliches if c.lower() in text.lower())

    return {
        "baseline_len_chars": len(baseline),
        "specialized_len_chars": len(specialized),
        "baseline_avg_sentence_words": round(avg_sentence_len(baseline), 1),
        "specialized_avg_sentence_words": round(avg_sentence_len(specialized), 1),
        "baseline_exclamations": count_exclamations(baseline),
        "specialized_exclamations": count_exclamations(specialized),
        "baseline_cliches": count_forbidden_cliches(baseline),
        "specialized_cliches": count_forbidden_cliches(specialized),
    }


def main():
    print("Loading catalog and building retriever...")
    songs = load_songs("data/songs.csv")
    retriever = SongRetriever(songs)
    print(f"Indexed {len(songs)} songs.\n")

    results = []

    for query in TEST_QUERIES:
        print("=" * 72)
        print(f"QUERY: {query}")
        print("=" * 72)

        # Run the pipeline once to get the picks (both voices commentate on the SAME picks)
        result = recommend(query, songs=songs, retriever=retriever, k=5)
        picks_text = "\n".join(
            f"- {s['title']} by {s['artist']} ({s['genre']}, {s['mood']}, "
            f"energy {s['energy']})"
            for s, _score, _reasons in result.recommendations
        )

        # Baseline commentary is already in result.commentary from the pipeline run
        baseline = result.commentary

        # Specialized commentary: same picks, persona-constrained voice
        specialized, _source = generate_persona_commentary(
            query, picks_text, PERSONA_CLERK
        )

        # Measure the difference
        metrics = measure_difference(baseline, specialized)

        print(f"\n--- BASELINE (warm music guide) ---")
        print(baseline)
        print(f"\n--- SPECIALIZED ({PERSONA_CLERK['name']}) ---")
        print(specialized)
        print(f"\n--- METRICS ---")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
        print()

        results.append({
            "query": query,
            "baseline": baseline,
            "specialized": specialized,
            "metrics": metrics,
        })

    # Aggregate summary
    print("=" * 72)
    print("AGGREGATE COMPARISON")
    print("=" * 72)
    avg = lambda k: round(sum(r["metrics"][k] for r in results) / len(results), 1)
    print(f"Avg sentence length (baseline):    {avg('baseline_avg_sentence_words')} words")
    print(f"Avg sentence length (specialized): {avg('specialized_avg_sentence_words')} words")
    print(f"Total exclamations (baseline):     {sum(r['metrics']['baseline_exclamations'] for r in results)}")
    print(f"Total exclamations (specialized):  {sum(r['metrics']['specialized_exclamations'] for r in results)}")
    print(f"Total cliches (baseline):          {sum(r['metrics']['baseline_cliches'] for r in results)}")
    print(f"Total cliches (specialized):       {sum(r['metrics']['specialized_cliches'] for r in results)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())