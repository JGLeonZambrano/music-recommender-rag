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

To evaluate the recommender, I ran three deliberately diverse user profiles against the same 18-song catalog, plus one "adversarial" profile designed to expose the system's weak spots:

### Three profile stress-test

Catalog size: 18 songs

======================================================================
Profile: High-Energy Pop (default)
Preferences: {'favorite_genre': 'pop', 'favorite_mood': 'happy', 'target_energy': 0.8, 'likes_acoustic': False}

Top 5 recommendations:

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

======================================================================
Profile: Chill Acoustic Listener
Preferences: {'favorite_genre': 'acoustic', 'favorite_mood': 'sad', 'target_energy': 0.2, 'likes_acoustic': True}

Top 5 recommendations:

  1. Rain on Glass by Paper Lanterns — Score: 6.46
     Because: genre match (acoustic) +1.5; mood match (sad) +2.0; energy 0.18 vs target 0.20 (+1.96); acoustic preference match (acoustic) +1.0

  2. Empty Apartment by Grey November — Score: 4.96
     Because: mood match (sad) +2.0; energy 0.22 vs target 0.20 (+1.96); acoustic preference match (acoustic) +1.0

  3. Spacewalk Thoughts by Orbit Bloom — Score: 2.84
     Because: energy 0.28 vs target 0.20 (+1.84); acoustic preference match (acoustic) +1.0

  4. Library Rain by Paper Lanterns — Score: 2.70
     Because: energy 0.35 vs target 0.20 (+1.70); acoustic preference match (acoustic) +1.0

  5. Coffee Shop Stories by Slow Stereo — Score: 2.66
     Because: energy 0.37 vs target 0.20 (+1.66); acoustic preference match (acoustic) +1.0

======================================================================
Profile: Hip-Hop Fan
Preferences: {'favorite_genre': 'hip-hop', 'favorite_mood': 'intense', 'target_energy': 0.85, 'likes_acoustic': False}

Top 5 recommendations:

  1. Concrete Bloom by Static Reign — Score: 6.44
     Because: genre match (hip-hop) +1.5; mood match (intense) +2.0; energy 0.88 vs target 0.85 (+1.94); acoustic preference match (non-acoustic) +1.0

  2. Neon Alibi by Voltline — Score: 4.98
     Because: mood match (intense) +2.0; energy 0.86 vs target 0.85 (+1.98); acoustic preference match (non-acoustic) +1.0

  3. Storm Runner by Voltline — Score: 4.88
     Because: mood match (intense) +2.0; energy 0.91 vs target 0.85 (+1.88); acoustic preference match (non-acoustic) +1.0

  4. Gym Hero by Max Pulse — Score: 4.84
     Because: mood match (intense) +2.0; energy 0.93 vs target 0.85 (+1.84); acoustic preference match (non-acoustic) +1.0

  5. Fault Lines by Redline Riot — Score: 4.80
     Because: mood match (intense) +2.0; energy 0.95 vs target 0.85 (+1.80); acoustic preference match (non-acoustic) +1.0

### What the outputs reveal

- **Each profile produces a genuinely different #1** — "Sunrise City" for the pop listener, "Rain on Glass" for the chill acoustic listener, "Concrete Bloom" for the hip-hop fan. The recommender is responsive to preferences, not returning generic results.

- **The mood weight (+2.0 > +1.5 genre) is visible in the ranking.** In the pop profile, "Rooftop Lights" (indie pop, happy) beats "Gym Hero" (pop, intense) at #2/#3 because mood matching outweighs the genre miss. This is a design choice showing up in behavior.

- **Sparse-genre falloff.** For the hip-hop fan, #2–#5 contain zero hip-hop songs: the catalog only has two hip-hop tracks, so after "Concrete Bloom" the recommender falls back on cross-genre songs that satisfy the other three rules (mood + energy + acoustic). The system doesn't fail, it degrades gracefully, but this is a real limitation of the small catalog.

### Adversarial experiment: conflicting preferences

I ran a fourth profile with contradictory preferences: a listener who wants "happy pop" but with LOW energy (0.2), i.e. mellow pop. Almost no such song exists in the catalog. This tests how the recommender behaves when a user's stated preferences pull in opposite irections.

======================================================================
EXPERIMENT: Adversarial profile (conflicting preferences)
======================================================================
A user who claims to want 'happy pop' but with LOW energy (0.2)
— i.e. mellow pop. Almost no such song exists in our catalog.

Preferences: {'favorite_genre': 'pop', 'favorite_mood': 'happy', 'target_energy': 0.2, 'likes_acoustic': False}

Top 5 recommendations:

  1. Sunrise City — Score: 5.26  (energy 0.82)
     genre match (pop) +1.5; mood match (happy) +2.0; energy 0.82 vs target 0.20 (+0.76); acoustic preference match (non-acoustic) +1.0

  2. Rooftop Lights — Score: 3.88  (energy 0.76)
     mood match (happy) +2.0; energy 0.76 vs target 0.20 (+0.88); acoustic preference match (non-acoustic) +1.0

  3. Gym Hero — Score: 3.04  (energy 0.93)
     genre match (pop) +1.5; energy 0.93 vs target 0.20 (+0.54); acoustic preference match (non-acoustic) +1.0

  4. Late Bus Home — Score: 2.30  (energy 0.55)
     energy 0.55 vs target 0.20 (+1.30); acoustic preference match (non-acoustic) +1.0

  5. Empty Apartment — Score: 1.96  (energy 0.22)
     energy 0.22 vs target 0.20 (+1.96)

### What the experiment reveals

- **Category matches dominate energy closeness by design.** "Sunrise City" still wins at #1 with an energy score of only +0.76 (energy 0.82 vs target 0.20, ie the opposite of what the user asked for), because its triple-category match (+1.5 genre, +2.0 mood, +1.0 acoustic) more than compensates. "Empty Apartment", which has near-perfect energy (0.22 vs 0.20 target, earning +1.96), lands at #5 because no categories match.

- **Design tension exposed.** This behavior is consistent with my recipe ("categories matter most"), but it is arguably wrong from a user experience angle: a listener explicitly requesting low energy may actually mean "I want mellow music right now" more than "I want my usual genre." A future version could treat energy as a *harder* constraint when it's very different from typical songs, rather than a soft slide.

- **The acoustic bonus is symmetric.** The +1.0 fires when the song matches whether the user `likes_acoustic`, including when `likes_acoustic=False`, so non-acoustic songs get a bonus for being non-acoustic. That likely inflates scores across the board and should probably only apply when `likes_acoustic=True`.

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



