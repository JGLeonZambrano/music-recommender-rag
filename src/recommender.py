from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    Thin OOP wrapper around the functional scoring/ranking logic.

    Exists so tests in tests/test_recommender.py can use a class-based
    interface while the core logic lives in the module-level functions
    load_songs, score_song, and recommend_songs.
    """

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects ranked by score for this user."""
        user_prefs = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        # Convert Song dataclasses to dicts so score_song can read them.
        song_dicts = [song.__dict__ for song in self.songs]
        ranked = recommend_songs(user_prefs, song_dicts, k=k)
        # Map back to the original Song objects preserving order.
        title_to_song = {s.title: s for s in self.songs}
        return [title_to_song[song_dict["title"]] for song_dict in [r[0] for r in ranked]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-language string explaining why this song ranks where it does."""
        user_prefs = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        _score, reasons = score_song(user_prefs, song.__dict__)
        return "; ".join(reasons) if reasons else "no matching features"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Load songs from a CSV file into a list of dicts.
    Numeric columns are converted from strings to numbers so scoring math works.
    """
    import csv

    numeric_int_cols = {"id"}
    numeric_float_cols = {"energy", "tempo_bpm", "valence", "danceability", "acousticness"}

    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for col in numeric_int_cols:
                row[col] = int(row[col])
            for col in numeric_float_cols:
                row[col] = float(row[col])
            songs.append(row)

    return songs

@dataclass
class ScoringStrategy:
    """
    A named bundle of scoring weights (a lightweight Strategy pattern).

    Each strategy is an interchangeable "ranking mode": swapping the strategy
    passed to score_song / recommend_songs changes how songs are ranked
    without touching the scoring logic itself. This keeps the algorithm
    modular — new modes are added by registering a new ScoringStrategy, not
    by editing score_song.
    """
    name: str
    genre_weight: float
    mood_weight: float
    energy_weight: float
    acoustic_weight: float

# Registry of selectable ranking modes. "balanced" reproduces the original
# recipe exactly, so default behaviour (and the test suite) is unchanged.
SCORING_MODES: Dict[str, ScoringStrategy] = {
    "balanced": ScoringStrategy("Balanced (default)", 1.5, 2.0, 2.0, 1.0),
    "genre-first": ScoringStrategy("Genre-First", 3.0, 1.0, 1.0, 0.5),
    "energy-similarity": ScoringStrategy("Energy-Similarity", 0.0, 0.0, 4.0, 0.0),
}

DEFAULT_STRATEGY = SCORING_MODES["balanced"]

def score_song(
    user_prefs: Dict,
    song: Dict,
    strategy: Optional[ScoringStrategy] = None,
) -> Tuple[float, List[str]]:
    """
    Score a single song against user preferences.

    Args:
        strategy: A ScoringStrategy selecting the ranking mode (weights).
            Defaults to the "balanced" strategy, which matches the original
            recipe below exactly.

    Returns:
        (score, reasons) - a float score and a list of human-readable
        strings explaining why each point was awarded.

    Balanced recipe (default weights):
      - Genre match:       +1.5
      - Mood match:        +2.0  (weighted higher because mood tracks
                                  the user's felt experience)
      - Energy closeness:  up to +2.0, sliding down as the gap grows
                           formula: energy_weight * (1 - |song_energy - target|)
      - Acoustic match:    +1.0 when the song's acousticness aligns
                           with the user's likes_acoustic preference
                           (treating acousticness >= 0.5 as "acoustic")
    """
    if strategy is None:
        strategy = DEFAULT_STRATEGY

    score = 0.0
    reasons: List[str] = []

    # --- Genre match (category) ---
    if strategy.genre_weight and song["genre"] == user_prefs.get("favorite_genre"):
        score += strategy.genre_weight
        reasons.append(f"genre match ({song['genre']}) +{strategy.genre_weight}")

    # --- Mood match (category) ---
    if strategy.mood_weight and song["mood"] == user_prefs.get("favorite_mood"):
        score += strategy.mood_weight
        reasons.append(f"mood match ({song['mood']}) +{strategy.mood_weight}")

    # --- Energy closeness (numeric) ---
    target_energy = user_prefs.get("target_energy")
    if strategy.energy_weight and target_energy is not None:
        gap = abs(song["energy"] - target_energy)
        closeness = 1.0 - gap  # gap is 0..1, so closeness is 1..0
        energy_points = strategy.energy_weight * closeness
        score += energy_points
        reasons.append(
            f"energy {song['energy']:.2f} vs target {target_energy:.2f} "
            f"(+{energy_points:.2f})"
        )

    # --- Acoustic match (boolean preference on numeric column) ---
    likes_acoustic = user_prefs.get("likes_acoustic")
    if strategy.acoustic_weight and likes_acoustic is not None:
        song_is_acoustic = song["acousticness"] >= 0.5
        if song_is_acoustic == likes_acoustic:
            score += strategy.acoustic_weight
            side = "acoustic" if likes_acoustic else "non-acoustic"
            reasons.append(f"acoustic preference match ({side}) +{strategy.acoustic_weight}")

    return (score, reasons)

def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    diversity_penalty: float = 0.0,
    strategy: Optional[ScoringStrategy] = None,
) -> List[Tuple[Dict, float, str]]:
    """
    Rank every song by score and return the top k.

    Args:
        strategy: A ScoringStrategy (ranking mode) passed through to
            score_song. Defaults to the "balanced" strategy, leaving the
            original ranking unchanged.
        diversity_penalty: If > 0, applies a greedy "artist penalty" during
            selection. Each time a song is chosen, every remaining song by an
            already-selected artist has its effective score reduced by
            diversity_penalty per prior appearance of that artist. This stops
            one artist from dominating the list (a simple guard against
            "filter bubbles"). When 0.0 (the default), behaviour is unchanged:
            a pure highest-score-first ranking.

    Returns:
        A list of (song, score, explanation) tuples. Length is
        min(k, len(songs)). When a penalty is applied, the reported score is
        the effective (post-penalty) score and the explanation notes it.
    """
    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, strategy)
        explanation = "; ".join(reasons) if reasons else "no matching features"
        scored.append((song, score, explanation))

    # Sort by score, highest first.
    scored.sort(key=lambda item: item[1], reverse=True)

    # Default path: pure score ranking (keeps existing tests/behaviour intact).
    if diversity_penalty <= 0:
        return scored[:k]

    # Diversity-aware path: greedy re-rank with an artist penalty.
    selected: List[Tuple[Dict, float, str]] = []
    remaining = scored[:]
    artist_counts: Dict[str, int] = {}

    while remaining and len(selected) < k:
        best_idx = 0
        best_effective = None
        for idx, (song, score, _explanation) in enumerate(remaining):
            penalty = diversity_penalty * artist_counts.get(song["artist"], 0)
            effective = score - penalty
            if best_effective is None or effective > best_effective:
                best_effective = effective
                best_idx = idx

        song, score, explanation = remaining.pop(best_idx)
        prior = artist_counts.get(song["artist"], 0)
        penalty = diversity_penalty * prior
        if penalty > 0:
            explanation = f"{explanation}; artist penalty (-{penalty:.2f})"
        artist_counts[song["artist"]] = prior + 1
        selected.append((song, score - penalty, explanation))

    return selected