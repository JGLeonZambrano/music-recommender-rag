"""
Retriever: semantic search over the song catalog.

Each song is turned into a short text "document" (title, artist, genre, mood, plus a mood/genre gloss) 
and embedded into a vector using sentence-transformers. A query gets embedded the same way, and cosine similarity 
returns the top-N closest songs.

Why two-stage retrieval matters: with 52 songs, the exact-match scorer alone could look at everything. But in a 
real system with millions of items, you can't score every item. Retrieval narrows the field cheaply, then the precise 
scorer picks the winner from the shortlist. We do the same here so the architecture is honest about what it would 
be at scale.

RAG Enhancement (stretch, +2): the corpus is multi-source. Song rows are augmented with a genre/mood glossary 
so semantic matches work on descriptive language ("rainy night") not just literal metadata.
"""
from dataclasses import dataclass
from functools import lru_cache
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from src.recommender import load_songs

# Small, fast, high-quality embedding model. ~90MB, runs on CPU.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Multi-source gloss: descriptive phrases per genre and mood that make the semantic embedding more useful. 
# This is what turns "rainy night" into a match for melancholy/acoustic songs, even though 
# neither the song rows nor the query contain the words "rainy" or "night".
GENRE_GLOSS = {
    "pop": "mainstream radio-friendly upbeat catchy vocal",
    "lofi": "chill relaxed study coffee-shop beats textured warm",
    "rock": "guitar-driven loud energetic band",
    "jazz": "smoky sophisticated improvisation brass strings",
    "hip-hop": "rap urban beats rhythmic verses",
    "indie": "independent alternative unpolished sincere",
    "indie pop": "independent alternative pop sincere melodic",
    "acoustic": "unplugged intimate guitar-based stripped-down",
    "folk": "storytelling acoustic traditional americana",
    "r&b": "smooth soul vocal groove late-night",
    "classical": "orchestral instrumental composition strings piano",
    "electronic": "synthesized dance-floor pulsing programmed",
    "punk": "fast aggressive raw rebellious",
    "tango": "sensual argentine bandoneón dance dramatic",
    "synthwave": "retro 80s synthesizer nostalgic neon",
    "ambient": "atmospheric spacious meditative background",
}

MOOD_GLOSS = {
    "happy": "cheerful uplifting bright sunny joyful",
    "sad": "downcast heavy quiet blue tearful",
    "chill": "calm relaxed easy laid-back mellow",
    "intense": "high-energy driving aggressive powerful",
    "angry": "furious hard confrontational cathartic",
    "melancholy": "wistful bittersweet rainy-night pensive lonely",
    "hopeful": "optimistic looking-forward light rising",
    "nostalgic": "memory-tinged bittersweet remembering old-photos",
    "moody": "brooding atmospheric dim complicated",
    "focused": "productive concentrated background flow-state",
    "relaxed": "unhurried peaceful still restorative",
}


@dataclass
class RetrievedSong:
    song: dict
    similarity: float
    document: str


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it. First call takes ~5s."""
    return SentenceTransformer(EMBEDDING_MODEL)


def _song_to_document(song: dict) -> str:
    """Turn a song row into a descriptive text document for embedding."""
    genre_gloss = GENRE_GLOSS.get(song["genre"], "")
    mood_gloss = MOOD_GLOSS.get(song["mood"], "")
    return (
        f"{song['title']} by {song['artist']}. "
        f"Genre: {song['genre']} ({genre_gloss}). "
        f"Mood: {song['mood']} ({mood_gloss})."
    )


class SongRetriever:
    """Semantic retriever over the song catalog. Build once, query many times."""

    def __init__(self, songs: List[dict]):
        self.songs = songs
        self.documents = [_song_to_document(s) for s in songs]
        model = _get_model()
        self.embeddings = model.encode(
            self.documents,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    def retrieve(self, query: str, top_n: int = 15) -> List[RetrievedSong]:
        """Return the top_n songs most semantically similar to the query."""
        model = _get_model()
        query_vec = model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]

        # Because vectors are normalized, dot product = cosine similarity.
        similarities = self.embeddings @ query_vec

        top_indices = np.argsort(-similarities)[:top_n]
        return [
            RetrievedSong(
                song=self.songs[i],
                similarity=float(similarities[i]),
                document=self.documents[i],
            )
            for i in top_indices
        ]


if __name__ == "__main__":
    print("Loading songs and building embeddings (first run downloads model ~90MB)...")
    songs = load_songs("data/songs.csv")
    retriever = SongRetriever(songs)
    print(f"Indexed {len(songs)} songs.\n")

    tests = [
        "something melancholy and acoustic for a rainy night",
        "gym workout, aggressive hip-hop",
        "smoky jazz for a late dinner",
        "80s throwback synthwave",
    ]
    for q in tests:
        print(f"Query: {q}")
        results = retriever.retrieve(q, top_n=5)
        for r in results:
            print(f"  {r.similarity:.3f}  {r.song['title']} — {r.song['artist']} "
                  f"[{r.song['genre']}/{r.song['mood']}]")
        print()