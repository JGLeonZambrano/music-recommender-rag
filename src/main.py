"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs, SCORING_MODES
from tabulate import tabulate

def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"\nCatalog size: {len(songs)} songs\n")

    profiles = {
        "High-Energy Pop (default)": {
            "favorite_genre": "pop",
            "favorite_mood": "happy",
            "target_energy": 0.8,
            "likes_acoustic": False,
        },
        "Chill Acoustic Listener": {
            "favorite_genre": "acoustic",
            "favorite_mood": "sad",
            "target_energy": 0.2,
            "likes_acoustic": True,
        },
        "Hip-Hop Fan": {
            "favorite_genre": "hip-hop",
            "favorite_mood": "intense",
            "target_energy": 0.85,
            "likes_acoustic": False,
        },
    }

    for name, user_prefs in profiles.items():
        print("=" * 70)
        print(f"Profile: {name}")
        print(f"Preferences: {user_prefs}\n")

        recommendations = recommend_songs(user_prefs, songs, k=5)

        print("Top 5 recommendations:\n")
        print(format_recommendations_table(recommendations, name))
        print()

def experiment_weight_shift() -> None:
    """
    Small sensitivity experiment: what if genre mattered more than mood?
    We can't easily change weights without editing score_song, so we
    demonstrate sensitivity a different way — by testing an "adversarial"
    profile whose energy target is deliberately far from any real song.
    """
    songs = load_songs("data/songs.csv")

    print("\n" + "=" * 70)
    print("EXPERIMENT: Adversarial profile (conflicting preferences)")
    print("=" * 70)
    print("A user who claims to want 'happy pop' but with LOW energy (0.2)")
    print("— i.e. mellow pop. Almost no such song exists in our catalog.\n")

    weird_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.2,       # ← the twist: happy pop is usually energetic
        "likes_acoustic": False,
    }
    print(f"Preferences: {weird_prefs}\n")

    recommendations = recommend_songs(weird_prefs, songs, k=5)
    print("Top 5 recommendations:\n")
    print(format_recommendations_table(recommendations, "Adversarial profile"))
    print()

def experiment_diversity_penalty() -> None:
    """
    Stretch: Diversity / Fairness. The default "High-Energy Pop" profile
    surfaces the same artist (Neon Echo) twice in its top 5. This demo runs
    that profile with the artist penalty OFF, then ON, so you can see the
    repetition get broken up in favour of a fresh artist.
    """
    songs = load_songs("data/songs.csv")

    prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    }

    print("\n" + "=" * 70)
    print("EXPERIMENT: Diversity / artist penalty (High-Energy Pop profile)")
    print("=" * 70)

    print("\nBEFORE — no penalty (pure score ranking):\n")
    baseline = recommend_songs(prefs, songs, k=5, diversity_penalty=0.0)
    print(format_recommendations_table(baseline, "No penalty"))

    print("\nAFTER — artist penalty = 1.0 per repeat:\n")
    diversified = recommend_songs(prefs, songs, k=5, diversity_penalty=1.0)
    print(format_recommendations_table(diversified, "Artist penalty"))
    print()

def format_recommendations_table(
    recommendations: list,
    profile_name: str,
) -> str:
    """
    Format recommendations as a nicely-aligned table using tabulate.
    Displays rank, title, artist, score, and the reasons for the score.
    """
    rows = []
    for i, (song, score, explanation) in enumerate(recommendations, start=1):
        rows.append([
            i,
            song["title"],
            song["artist"],
            f"{score:.2f}",
            explanation,
        ])

    headers = ["#", "Title", "Artist", "Score", "Reasons"]
    return tabulate(rows, headers=headers, tablefmt="rounded_grid", maxcolwidths=[3, 22, 20, 7, 60])

def experiment_ranking_modes() -> None:
    """
    Stretch: Multiple ranking modes via a Strategy pattern. Runs the same
    High-Energy Pop profile through three interchangeable scoring strategies
    so you can see how the same listener gets ranked differently depending
    on which mode is active.
    """
    songs = load_songs("data/songs.csv")

    prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    }

    print("\n" + "=" * 70)
    print("EXPERIMENT: Ranking modes (Strategy pattern) — High-Energy Pop")
    print("=" * 70)

    for mode_key in ("balanced", "genre-first", "energy-similarity"):
        strategy = SCORING_MODES[mode_key]
        print(f"\nMode: {strategy.name}  [key='{mode_key}']\n")
        recs = recommend_songs(prefs, songs, k=3, strategy=strategy)
        print(format_recommendations_table(recs, strategy.name))
    print()

if __name__ == "__main__":
    main()
    experiment_weight_shift()
    experiment_diversity_penalty()
    experiment_ranking_modes()