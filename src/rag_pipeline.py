"""
RAG pipeline: the end-to-end music recommendation system.

Flow:
    NL query
      -> intent parser (LLM extracts structured user_prefs)
      -> retriever (semantic search returns top-N candidates)
      -> recommend_songs (structured scorer picks final top-k from candidates)
      -> Gemini writes grounded commentary about the picks
      -> return (recommendations, commentary, trace)

Key design decision: the LLM parses input and writes output prose, but it never selects songs. 
Selection is always done by the deterministic structured scorer over a retrieved candidate set. This makes the system
resistant to hallucination: the LLM cannot recommend a song that isn't in the catalog because it never picks.

The 'trace' field records every stage's output so we can inspect intermediate reasoning (required for the 
Agentic Workflow stretch and for the model card's transparency section).
"""
from dataclasses import dataclass, field
from typing import List, Optional
from src.recommender import load_songs, recommend_songs
from src.retriever import SongRetriever, RetrievedSong
from src.intent_parser import parse_query
from src.llm_client import generate


COMMENTARY_PROMPT = """You are a knowledgeable music guide helping someone find songs.

The user asked: "{query}"

Our system retrieved and ranked these songs from the catalog:

{picks}

Write a short, warm paragraph (3-5 sentences) explaining why these songs match the request. 
Reference specific songs by title and artist. Do NOT recommend any song not in the list above. Do NOT invent songs or artists.
"""


@dataclass
class RagResult:
    query: str
    user_prefs: dict
    retrieved: List[RetrievedSong]
    recommendations: List[tuple]
    commentary: str
    trace: dict = field(default_factory=dict)


def recommend(
    query: str,
    songs: Optional[List[dict]] = None,
    retriever: Optional[SongRetriever] = None,
    k: int = 5,
    top_n_retrieved: int = 15,
    diversity_penalty: float = 0.0,
) -> RagResult:
    """
    Run the full RAG pipeline on one query.

    Args:
        songs: optional pre-loaded song list (avoids re-reading CSV).
        retriever: optional pre-built SongRetriever (avoids re-embedding).
        k: how many final recommendations to return.
        top_n_retrieved: how many candidates retrieval returns for scoring.
        diversity_penalty: passed through to recommend_songs (artist penalty).
    """
    trace = {"stages": []}

    if songs is None:
        songs = load_songs("data/songs.csv")
    if retriever is None:
        retriever = SongRetriever(songs)

    # Stage 1: parse the natural-language query
    user_prefs, parser_source = parse_query(query)
    trace["stages"].append({
        "stage": "intent_parser",
        "source": parser_source,
        "output": user_prefs,
    })

    # Stage 2: retrieve top-N semantically similar candidates
    retrieved = retriever.retrieve(query, top_n=top_n_retrieved)
    trace["stages"].append({
        "stage": "retriever",
        "candidates_returned": len(retrieved),
        "top_titles": [r.song["title"] for r in retrieved[:5]],
    })

    # Stage 3: structured scorer picks final top-k from retrieved candidates
    candidate_songs = [r.song for r in retrieved]
    recommendations = recommend_songs(
        user_prefs,
        candidate_songs,
        k=k,
        diversity_penalty=diversity_penalty,
    )
    trace["stages"].append({
        "stage": "structured_scorer",
        "picks": [(s["title"], round(score, 2)) for s, score, _ in recommendations],
    })

    # Stage 4: LLM writes grounded commentary about the picks
    picks_text = "\n".join(
        f"- {s['title']} by {s['artist']} ({s['genre']}, {s['mood']}, "
        f"energy {s['energy']}) — reasons: {reasons}"
        for s, _score, reasons in recommendations
    )
    prompt = COMMENTARY_PROMPT.format(query=query, picks=picks_text)
    commentary, llm_source = generate(prompt)
    trace["stages"].append({
        "stage": "llm_commentary",
        "source": llm_source,
    })

    return RagResult(
        query=query,
        user_prefs=user_prefs,
        retrieved=retrieved,
        recommendations=recommendations,
        commentary=commentary,
        trace=trace,
    )


if __name__ == "__main__":
    print("Loading catalog and building retriever (one-time setup)...\n")
    songs = load_songs("data/songs.csv")
    retriever = SongRetriever(songs)

    queries = [
        "something melancholy and acoustic for a rainy night",
        "high-energy hip-hop for a workout",
        "smoky jazz for a late dinner with friends",
    ]

    for q in queries:
        print("=" * 72)
        print(f"QUERY: {q}\n")
        result = recommend(q, songs=songs, retriever=retriever, k=5)

        print(f"Parsed preferences: {result.user_prefs}\n")

        print("Top 5 recommendations:")
        for i, (song, score, reasons) in enumerate(result.recommendations, 1):
            print(f"  {i}. {song['title']} — {song['artist']} "
                  f"({song['genre']}/{song['mood']}) score={score:.2f}")
            print(f"     reasons: {reasons}")

        print(f"\nCommentary:\n{result.commentary}\n")