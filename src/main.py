"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs

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
        for i, (song, score, explanation) in enumerate(recommendations, start=1):
            print(f"  {i}. {song['title']} by {song['artist']} — Score: {score:.2f}")
            print(f"     Because: {explanation}\n")

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
    for i, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"  {i}. {song['title']} — Score: {score:.2f}  (energy {song['energy']})")
        print(f"     {explanation}\n")


if __name__ == "__main__":
    main()
    experiment_weight_shift()