# 🎵 Music Recommender Simulation

## Project Summary

This project builds a small **content-based** music recommender. It reads a catalog of 18 songs from `data/songs.csv`, scores each one against a listener's taste profile (favorite genre, favorite mood, target energy, and acoustic preference), and returns the top *k* ranked songs along with plain-language reasons for each recommendation.

---

## How The System Works

This project is a **content-based** music recommender. It looks at the attributes of each song and matches them against a single user's stated taste. In other words: "this song is *like* the songs you already like."

This is different from **collaborative filtering**, the approach behind apps like Spotify's Discover Weekly, which ignores song attributes and instead looks at the behavior of a *crowd*: "people who listen to what you listen to also loved this." 
Collaborative filtering isn't just unused here, it's impossible: I only have data for one user and no record of any crowd's listening behavior, so I must match on song attributes instead.

Every content-based recommender works in three stages:

1. **Input data** — objective facts about each song (its columns in `songs.csv`: genre, mood, energy, etc.).
2. **User preferences** — what *this* listener wants, stored as a taste profile (e.g. favorite genre, favorite mood, target energy).
3. **Ranking / selection** — the logic that scores each song against the user's preferences and sorts them to pick the best few.

### Features my system uses

My `Song` objects carry several attributes, but my recommender scores on **four** of them:

- **genre** (category) — does the song's genre match the user's favorite?
- **mood** (category) — does the song's mood match the user's favorite?
- **energy** (numeric, 0.0–1.0) — how *close* is the song's energy to the user's target?
- **acousticness** (numeric, 0.0–1.0) — folded in via the user's `likes_acoustic` preference.

I deliberately left out two available columns:
1) **tempo_bpm**, because it overlaps heavily with energy (fast songs tend to feel energetic) and would double-count the same "vibe"; and 
2) **valence** (a song's happy-vs-sad measure), which I set aside to keep the first version focused and may add later.

My `UserProfile` stores: favorite_genre, favorite_mood, target_energy, and likes_acoustic.

### Scoring Recipe

Each song earns points from four rules; its total score is the sum of whichever apply.

- **Genre match:** +1.5 if the song's genre equals the user's favorite genre.
- **Mood match:** +2.0 if the song's mood equals the user's favorite mood.
  (Weighted higher than genre because mood tracks the user's felt experience, which is what a "vibe" recommender is really trying to match.)
- **Energy closeness:** up to +2.0, based on how close the song's energy is to the user's target. A perfect match earns the full 2.0; the reward slides down toward 0 as the gap grows (formula: `2.0 × (1 − |song − target|)`).
- **Acoustic bonus:** +1.0 when the song's acousticness aligns with the user's `likes_acoustic` preference (treating acousticness ≥ 0.5 as "acoustic").

**Scoring vs Ranking.** The scoring rule above judges a *single* song. The ranking rule then applies that score to every song in the catalog and sorts them high-to-low, returning the top *k* as recommendations. Scoring produces a number; ranking picks the winners.

### Biases I Expect

Because mood is my highest-weighted feature (+2.0), the system will over-privilege mood matches (a "happy" song in the wrong genre may still outrank a genre-perfect song with a different mood). Because I only score four features, the system also can't distinguish between two songs that match on all four but differ on, say, tempo or valence. And because my catalog only holds 18 songs across a handful of genres, any profile whose favorite_genre isn't well-represented will get shallow, repetitive results.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

## Sample Recommendation Output

Running `python -m src.main` with the default pop/happy/high-energy
listener profile produces:

```
User profile: {'favorite_genre': 'pop', 'favorite_mood': 'happy', 'target_energy': 0.8, 'likes_acoustic': False}
Catalog size: 18 songs

Top recommendations:

1. Sunrise City by Neon Echo — Score: 6.46
   Because: genre match (pop) +1.5; mood match (happy) +2.0; energy 0.82 vs target 0.80 (+1.96); acoustic preference match (non-acoustic) +1.0

2. Rooftop Lights by Indigo Parade — Score: 4.92
   Because: mood match (happy) +2.0; energy 0.76 vs target 0.80 (+1.92); acoustic preference match (non-acoustic) +1.0

3. Gym Hero by Max Pulse — Score: 4.24
   Because: genre match (pop) +1.5; energy 0.93 vs target 0.80 (+1.74); acoustic preference match (non-acoustic) +1.0

4. Night Drive Loop by Neon Echo — Score: 2.90
   Because: energy 0.75 vs target 0.80 (+1.90); acoustic preference match (non-acoustic) +1.0

5. Neon Alibi by Voltline — Score: 2.88
   Because: energy 0.86 vs target 0.80 (+1.88); acoustic preference match (non-acoustic) +1.0
```

Notice how the ranking reflects the scoring weights: Rooftop Lights beats Gym Hero despite not matching on genre, because the mood weight (+2.0) is higher than the genre weight (+1.5) in my recipe — a deliberate design choice consistent with treating "vibe" as more central than "category."

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



