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

    # Default profile: a pop/happy listener with high energy, not acoustic
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    }

    print(f"\nUser profile: {user_prefs}")
    print(f"Catalog size: {len(songs)} songs\n")

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("Top recommendations:\n")
    for i, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{i}. {song['title']} by {song['artist']} — Score: {score:.2f}")
        print(f"   Because: {explanation}\n")


if __name__ == "__main__":
    main()
