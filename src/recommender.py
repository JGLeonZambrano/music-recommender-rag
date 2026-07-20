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
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

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

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Score a single song against user preferences.

    Returns:
        (score, reasons) - a float score and a list of human-readable
        strings explaining why each point was awarded.

    Scoring recipe:
      - Genre match:       +1.5
      - Mood match:        +2.0  (weighted higher because mood tracks
                                  the user's felt experience)
      - Energy closeness:  up to +2.0, sliding down as the gap grows
                           formula: 2.0 * (1 - |song_energy - target|)
      - Acoustic match:    +1.0 when the song's acousticness aligns
                           with the user's likes_acoustic preference
                           (treating acousticness >= 0.5 as "acoustic")
    """
    score = 0.0
    reasons: List[str] = []

    # --- Genre match (category) ---
    if song["genre"] == user_prefs.get("favorite_genre"):
        score += 1.5
        reasons.append(f"genre match ({song['genre']}) +1.5")

    # --- Mood match (category) ---
    if song["mood"] == user_prefs.get("favorite_mood"):
        score += 2.0
        reasons.append(f"mood match ({song['mood']}) +2.0")

    # --- Energy closeness (numeric) ---
    target_energy = user_prefs.get("target_energy")
    if target_energy is not None:
        gap = abs(song["energy"] - target_energy)
        closeness = 1.0 - gap  # gap is 0..1, so closeness is 1..0
        energy_points = 2.0 * closeness
        score += energy_points
        reasons.append(
            f"energy {song['energy']:.2f} vs target {target_energy:.2f} "
            f"(+{energy_points:.2f})"
        )

    # --- Acoustic match (boolean preference on numeric column) ---
    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None:
        song_is_acoustic = song["acousticness"] >= 0.5
        if song_is_acoustic == likes_acoustic:
            score += 1.0
            side = "acoustic" if likes_acoustic else "non-acoustic"
            reasons.append(f"acoustic preference match ({side}) +1.0")

    return (score, reasons)

def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
) -> List[Tuple[Dict, float, str]]:
    """
    Rank every song by score and return the top k.

    Returns:
        A list of (song, score, explanation) tuples, sorted from
        highest score to lowest. Length is min(k, len(songs)).
    """
    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = "; ".join(reasons) if reasons else "no matching features"
        scored.append((song, score, explanation))

    # Sort by score, highest first.
    scored.sort(key=lambda item: item[1], reverse=True)

    return scored[:k]
