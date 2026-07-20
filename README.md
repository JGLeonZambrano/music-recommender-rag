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

### Diversity / Artist Penalty (optional)

`recommend_songs` accepts an optional `diversity_penalty` argument (default `0.0`, off). When set above zero, the ranker applies a greedy **artist penalty**: each time a song is selected, any remaining song by an already-chosen artist has its effective score reduced by the penalty per prior appearance. This prevents a single artist from dominating the Top-5 (a simple guard against "filter bubbles"). With the penalty off, behavior is a pure highest-score-first ranking, so existing tests are unaffected. See the diversity experiment below for a before/after.

### Ranking Modes (Strategy pattern)

Scoring weights are bundled into named **`ScoringStrategy`** objects and registered in `SCORING_MODES`. Each is an interchangeable *ranking mode* — passing a different strategy to `recommend_songs` changes how songs are ranked without editing the scoring logic (a lightweight Strategy pattern). Three modes ship:

- **Balanced (default)** — genre 1.5, mood 2.0, energy 2.0, acoustic 1.0. Identical to the original recipe.
- **Genre-First** — genre 3.0, mood/energy 1.0, acoustic 0.5. Exact-genre matches dominate.
- **Energy-Similarity** — energy 4.0, everything else 0. Ranks purely by how close a song's energy is to the target.

A user switches modes in `main.py` by selecting a key from `SCORING_MODES`.

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
   ```

2. Install dependencies:

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

Running `python -m src.main` with the default pop / happy / high-energy listener profile produces a formatted table (via `tabulate`) showing each recommendation's rank, title, artist, score, and the specific reasons the score was awarded:

```
======================================================================
Profile: High-Energy Pop (default)
Preferences: {'favorite_genre': 'pop', 'favorite_mood': 'happy', 'target_energy': 0.8, 'likes_acoustic': False}

Top 5 recommendations:

╭─────┬──────────────────┬───────────────┬─────────┬──────────────────────────────────────────────────────────────╮
│   # │ Title            │ Artist        │   Score │ Reasons                                                      │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   1 │ Sunrise City     │ Neon Echo     │    6.46 │ genre match (pop) +1.5; mood match (happy) +2.0; energy 0.82 │
│     │                  │               │         │ vs target 0.80 (+1.96); acoustic preference match (non-      │
│     │                  │               │         │ acoustic) +1.0                                               │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   2 │ Rooftop Lights   │ Indigo Parade │    4.92 │ mood match (happy) +2.0; energy 0.76 vs target 0.80 (+1.92); │
│     │                  │               │         │ acoustic preference match (non-acoustic) +1.0                │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   3 │ Gym Hero         │ Max Pulse     │    4.24 │ genre match (pop) +1.5; energy 0.93 vs target 0.80 (+1.74);  │
│     │                  │               │         │ acoustic preference match (non-acoustic) +1.0                │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   4 │ Night Drive Loop │ Neon Echo     │    2.9  │ energy 0.75 vs target 0.80 (+1.90); acoustic preference      │
│     │                  │               │         │ match (non-acoustic) +1.0                                    │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   5 │ Neon Alibi       │ Voltline      │    2.88 │ energy 0.86 vs target 0.80 (+1.88); acoustic preference      │
│     │                  │               │         │ match (non-acoustic) +1.0                                    │
╰─────┴──────────────────┴───────────────┴─────────┴──────────────────────────────────────────────────────────────╯
```

Notice how the ranking reflects the scoring weights: "Rooftop Lights" beats "Gym Hero" despite not matching on genre, because the mood weight (+2.0) is higher than the genre weight (+1.5) in my recipe, a deliberate design choice consistent with treating "vibe" as more central than "category."

---

## Experiments

To evaluate the recommender, I ran three deliberately diverse user profiles against the same 18-song catalog, plus one "adversarial" profile designed to expose the system's weak spots, plus a diversity experiment.

### Three-profile stress test

```
======================================================================
Profile: High-Energy Pop (default)
Preferences: {'favorite_genre': 'pop', 'favorite_mood': 'happy', 'target_energy': 0.8, 'likes_acoustic': False}

Top 5 recommendations:

╭─────┬──────────────────┬───────────────┬─────────┬──────────────────────────────────────────────────────────────╮
│   # │ Title            │ Artist        │   Score │ Reasons                                                      │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   1 │ Sunrise City     │ Neon Echo     │    6.46 │ genre match (pop) +1.5; mood match (happy) +2.0; energy 0.82 │
│     │                  │               │         │ vs target 0.80 (+1.96); acoustic preference match (non-      │
│     │                  │               │         │ acoustic) +1.0                                               │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   2 │ Rooftop Lights   │ Indigo Parade │    4.92 │ mood match (happy) +2.0; energy 0.76 vs target 0.80 (+1.92); │
│     │                  │               │         │ acoustic preference match (non-acoustic) +1.0                │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   3 │ Gym Hero         │ Max Pulse     │    4.24 │ genre match (pop) +1.5; energy 0.93 vs target 0.80 (+1.74);  │
│     │                  │               │         │ acoustic preference match (non-acoustic) +1.0                │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   4 │ Night Drive Loop │ Neon Echo     │    2.9  │ energy 0.75 vs target 0.80 (+1.90); acoustic preference      │
│     │                  │               │         │ match (non-acoustic) +1.0                                    │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   5 │ Neon Alibi       │ Voltline      │    2.88 │ energy 0.86 vs target 0.80 (+1.88); acoustic preference      │
│     │                  │               │         │ match (non-acoustic) +1.0                                    │
╰─────┴──────────────────┴───────────────┴─────────┴──────────────────────────────────────────────────────────────╯

======================================================================
Profile: Chill Acoustic Listener
Preferences: {'favorite_genre': 'acoustic', 'favorite_mood': 'sad', 'target_energy': 0.2, 'likes_acoustic': True}

Top 5 recommendations:

╭─────┬─────────────────────┬────────────────┬─────────┬────────────────────────────────────────────────────────────╮
│   # │ Title               │ Artist         │   Score │ Reasons                                                    │
├─────┼─────────────────────┼────────────────┼─────────┼────────────────────────────────────────────────────────────┤
│   1 │ Rain on Glass       │ Paper Lanterns │    6.46 │ genre match (acoustic) +1.5; mood match (sad) +2.0; energy │
│     │                     │                │         │ 0.18 vs target 0.20 (+1.96); acoustic preference match     │
│     │                     │                │         │ (acoustic) +1.0                                            │
├─────┼─────────────────────┼────────────────┼─────────┼────────────────────────────────────────────────────────────┤
│   2 │ Empty Apartment     │ Grey November  │    4.96 │ mood match (sad) +2.0; energy 0.22 vs target 0.20 (+1.96); │
│     │                     │                │         │ acoustic preference match (acoustic) +1.0                  │
├─────┼─────────────────────┼────────────────┼─────────┼────────────────────────────────────────────────────────────┤
│   3 │ Spacewalk Thoughts  │ Orbit Bloom    │    2.84 │ energy 0.28 vs target 0.20 (+1.84); acoustic preference    │
│     │                     │                │         │ match (acoustic) +1.0                                      │
├─────┼─────────────────────┼────────────────┼─────────┼────────────────────────────────────────────────────────────┤
│   4 │ Library Rain        │ Paper Lanterns │    2.7  │ energy 0.35 vs target 0.20 (+1.70); acoustic preference    │
│     │                     │                │         │ match (acoustic) +1.0                                      │
├─────┼─────────────────────┼────────────────┼─────────┼────────────────────────────────────────────────────────────┤
│   5 │ Coffee Shop Stories │ Slow Stereo    │    2.66 │ energy 0.37 vs target 0.20 (+1.66); acoustic preference    │
│     │                     │                │         │ match (acoustic) +1.0                                      │
╰─────┴─────────────────────┴────────────────┴─────────┴────────────────────────────────────────────────────────────╯

======================================================================
Profile: Hip-Hop Fan
Preferences: {'favorite_genre': 'hip-hop', 'favorite_mood': 'intense', 'target_energy': 0.85, 'likes_acoustic': False}

Top 5 recommendations:

╭─────┬────────────────┬──────────────┬─────────┬─────────────────────────────────────────────────────────╮
│   # │ Title          │ Artist       │   Score │ Reasons                                                 │
├─────┼────────────────┼──────────────┼─────────┼─────────────────────────────────────────────────────────┤
│   1 │ Concrete Bloom │ Static Reign │    6.44 │ genre match (hip-hop) +1.5; mood match (intense) +2.0;  │
│     │                │              │         │ energy 0.88 vs target 0.85 (+1.94); acoustic preference │
│     │                │              │         │ match (non-acoustic) +1.0                               │
├─────┼────────────────┼──────────────┼─────────┼─────────────────────────────────────────────────────────┤
│   2 │ Neon Alibi     │ Voltline     │    4.98 │ mood match (intense) +2.0; energy 0.86 vs target 0.85   │
│     │                │              │         │ (+1.98); acoustic preference match (non-acoustic) +1.0  │
├─────┼────────────────┼──────────────┼─────────┼─────────────────────────────────────────────────────────┤
│   3 │ Storm Runner   │ Voltline     │    4.88 │ mood match (intense) +2.0; energy 0.91 vs target 0.85   │
│     │                │              │         │ (+1.88); acoustic preference match (non-acoustic) +1.0  │
├─────┼────────────────┼──────────────┼─────────┼─────────────────────────────────────────────────────────┤
│   4 │ Gym Hero       │ Max Pulse    │    4.84 │ mood match (intense) +2.0; energy 0.93 vs target 0.85   │
│     │                │              │         │ (+1.84); acoustic preference match (non-acoustic) +1.0  │
├─────┼────────────────┼──────────────┼─────────┼─────────────────────────────────────────────────────────┤
│   5 │ Fault Lines    │ Redline Riot │    4.8  │ mood match (intense) +2.0; energy 0.95 vs target 0.85   │
│     │                │              │         │ (+1.80); acoustic preference match (non-acoustic) +1.0  │
╰─────┴────────────────┴──────────────┴─────────┴─────────────────────────────────────────────────────────╯
```

**What the outputs reveal**

- **Each profile produces a genuinely different #1** — *Sunrise City* for the pop listener, *Rain on Glass* for the chill acoustic listener, *Concrete Bloom* for the hip-hop fan. The recommender is responsive to preferences, not returning generic results.
- **The mood weight (+2.0 > +1.5 genre) is visible in the ranking.** In the pop profile, *Rooftop Lights* (indie pop, happy) beats *Gym Hero* (pop, intense) because mood matching outweighs the genre miss. A design choice showing up in behavior.
- **Sparse-genre falloff.** For the hip-hop fan, #2–#5 contain zero hip-hop songs: the catalog only has two hip-hop tracks, so after *Concrete Bloom* the recommender falls back on cross-genre songs that satisfy the other three rules. The system doesn't fail — it degrades gracefully — but this is a real limitation of the small catalog.

### Adversarial experiment: conflicting preferences

A fourth profile with contradictory preferences: a listener who wants "happy pop" but with LOW energy (0.2). Almost no such song exists in the catalog. This tests how the recommender behaves when a user's stated preferences pull in opposite directions.

```
======================================================================
EXPERIMENT: Adversarial profile (conflicting preferences)
======================================================================
A user who claims to want 'happy pop' but with LOW energy (0.2)
— i.e. mellow pop. Almost no such song exists in our catalog.

Preferences: {'favorite_genre': 'pop', 'favorite_mood': 'happy', 'target_energy': 0.2, 'likes_acoustic': False}

Top 5 recommendations:

╭─────┬─────────────────┬───────────────┬─────────┬──────────────────────────────────────────────────────────────╮
│   # │ Title           │ Artist        │   Score │ Reasons                                                      │
├─────┼─────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   1 │ Sunrise City    │ Neon Echo     │    5.26 │ genre match (pop) +1.5; mood match (happy) +2.0; energy 0.82 │
│     │                 │               │         │ vs target 0.20 (+0.76); acoustic preference match (non-      │
│     │                 │               │         │ acoustic) +1.0                                               │
├─────┼─────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   2 │ Rooftop Lights  │ Indigo Parade │    3.88 │ mood match (happy) +2.0; energy 0.76 vs target 0.20 (+0.88); │
│     │                 │               │         │ acoustic preference match (non-acoustic) +1.0                │
├─────┼─────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   3 │ Gym Hero        │ Max Pulse     │    3.04 │ genre match (pop) +1.5; energy 0.93 vs target 0.20 (+0.54);  │
│     │                 │               │         │ acoustic preference match (non-acoustic) +1.0                │
├─────┼─────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   4 │ Late Bus Home   │ Bluewire      │    2.3  │ energy 0.55 vs target 0.20 (+1.30); acoustic preference      │
│     │                 │               │         │ match (non-acoustic) +1.0                                    │
├─────┼─────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   5 │ Empty Apartment │ Grey November │    1.96 │ energy 0.22 vs target 0.20 (+1.96)                           │
╰─────┴─────────────────┴───────────────┴─────────┴──────────────────────────────────────────────────────────────╯
```

**What the experiment reveals**

- **Category matches dominate energy closeness by design.**
"Sunrise City" still wins at #1 with an energy score of only +0.76 (energy 0.82 vs target 0.20 — the opposite of what the user asked for), because its triple-category match more than compensates. *Empty Apartment*, with near-perfect energy (0.22 vs 0.20, earning +1.96), lands at #5 because no categories match.
- **Design tension exposed.** This is consistent with my recipe ("categories matter most"), but arguably wrong from a UX angle: a listener explicitly requesting low energy may mean "I want mellow music right now" more than "I want my usual genre."
- **The acoustic bonus is symmetric.** The +1.0 fires whenever the song matches `likes_acoustic`, including when it's `False`, so non-acoustic songs get a bonus for being non-acoustic. This likely inflates scores across the board and should probably only apply when `likes_acoustic=True`.

### Diversity experiment: artist penalty (stretch)

The default High-Energy Pop profile surfaces the **same artist (Neon Echo) twice** in its Top-5 — *Sunrise City* at #1 and *Night Drive Loop* at #4. Running the same profile with `diversity_penalty=1.0` breaks up that repetition.

**BEFORE — no penalty (pure score ranking):**

```
╭─────┬──────────────────┬───────────────┬─────────┬──────────────────────────────────────────────────────────────╮
│   # │ Title            │ Artist        │   Score │ Reasons                                                      │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   1 │ Sunrise City     │ Neon Echo     │    6.46 │ genre match (pop) +1.5; mood match (happy) +2.0; energy 0.82 │
│     │                  │               │         │ vs target 0.80 (+1.96); acoustic preference match (non-      │
│     │                  │               │         │ acoustic) +1.0                                               │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   2 │ Rooftop Lights   │ Indigo Parade │    4.92 │ mood match (happy) +2.0; energy 0.76 vs target 0.80 (+1.92); │
│     │                  │               │         │ acoustic preference match (non-acoustic) +1.0                │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   3 │ Gym Hero         │ Max Pulse     │    4.24 │ genre match (pop) +1.5; energy 0.93 vs target 0.80 (+1.74);  │
│     │                  │               │         │ acoustic preference match (non-acoustic) +1.0                │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   4 │ Night Drive Loop │ Neon Echo     │    2.9  │ energy 0.75 vs target 0.80 (+1.90); acoustic preference      │
│     │                  │               │         │ match (non-acoustic) +1.0                                    │
├─────┼──────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   5 │ Neon Alibi       │ Voltline      │    2.88 │ energy 0.86 vs target 0.80 (+1.88); acoustic preference      │
│     │                  │               │         │ match (non-acoustic) +1.0                                    │
╰─────┴──────────────────┴───────────────┴─────────┴──────────────────────────────────────────────────────────────╯
```

**AFTER — artist penalty = 1.0 per repeat:**

```
╭─────┬────────────────┬───────────────┬─────────┬──────────────────────────────────────────────────────────────╮
│   # │ Title          │ Artist        │   Score │ Reasons                                                      │
├─────┼────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   1 │ Sunrise City   │ Neon Echo     │    6.46 │ genre match (pop) +1.5; mood match (happy) +2.0; energy 0.82 │
│     │                │               │         │ vs target 0.80 (+1.96); acoustic preference match (non-      │
│     │                │               │         │ acoustic) +1.0                                               │
├─────┼────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   2 │ Rooftop Lights │ Indigo Parade │    4.92 │ mood match (happy) +2.0; energy 0.76 vs target 0.80 (+1.92); │
│     │                │               │         │ acoustic preference match (non-acoustic) +1.0                │
├─────┼────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   3 │ Gym Hero       │ Max Pulse     │    4.24 │ genre match (pop) +1.5; energy 0.93 vs target 0.80 (+1.74);  │
│     │                │               │         │ acoustic preference match (non-acoustic) +1.0                │
├─────┼────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   4 │ Neon Alibi     │ Voltline      │    2.88 │ energy 0.86 vs target 0.80 (+1.88); acoustic preference      │
│     │                │               │         │ match (non-acoustic) +1.0                                    │
├─────┼────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   5 │ Concrete Bloom │ Static Reign  │    2.84 │ energy 0.88 vs target 0.80 (+1.84); acoustic preference      │
│     │                │               │         │ match (non-acoustic) +1.0                                    │
╰─────┴────────────────┴───────────────┴─────────┴──────────────────────────────────────────────────────────────╯
```

**What the experiment reveals**

- With the penalty on, Neon Echo's second song (*Night Drive Loop*) is pushed out of the Top-5 and replaced by *Concrete Bloom* (Static Reign), so **every artist in the list is now unique**.
- The #1 pick is unchanged — the strongest match still wins. The penalty only affects *repeat* appearances, so it improves variety without sacrificing the top result.
- This is a small, transparent guard against "filter bubbles": in a real product, a listener who liked one Neon Echo track shouldn't have their whole feed become Neon Echo.

### Ranking-modes experiment: same listener, three strategies (stretch)

The same High-Energy Pop profile, ranked three different ways by swapping the scoring strategy. Each mode produces a **different Top-3**, showing the ranking is driven by the selected strategy, not hard-coded:

```
======================================================================
EXPERIMENT: Ranking modes (Strategy pattern) — High-Energy Pop
======================================================================

Mode: Balanced (default)  [key='balanced']

╭─────┬────────────────┬───────────────┬─────────┬──────────────────────────────────────────────────────────────╮
│   # │ Title          │ Artist        │   Score │ Reasons                                                      │
├─────┼────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   1 │ Sunrise City   │ Neon Echo     │    6.46 │ genre match (pop) +1.5; mood match (happy) +2.0; energy 0.82 │
│     │                │               │         │ vs target 0.80 (+1.96); acoustic preference match (non-      │
│     │                │               │         │ acoustic) +1.0                                               │
├─────┼────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   2 │ Rooftop Lights │ Indigo Parade │    4.92 │ mood match (happy) +2.0; energy 0.76 vs target 0.80 (+1.92); │
│     │                │               │         │ acoustic preference match (non-acoustic) +1.0                │
├─────┼────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   3 │ Gym Hero       │ Max Pulse     │    4.24 │ genre match (pop) +1.5; energy 0.93 vs target 0.80 (+1.74);  │
│     │                │               │         │ acoustic preference match (non-acoustic) +1.0                │
╰─────┴────────────────┴───────────────┴─────────┴──────────────────────────────────────────────────────────────╯

Mode: Genre-First  [key='genre-first']

╭─────┬────────────────┬───────────────┬─────────┬──────────────────────────────────────────────────────────────╮
│   # │ Title          │ Artist        │   Score │ Reasons                                                      │
├─────┼────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   1 │ Sunrise City   │ Neon Echo     │    5.48 │ genre match (pop) +3.0; mood match (happy) +1.0; energy 0.82 │
│     │                │               │         │ vs target 0.80 (+0.98); acoustic preference match (non-      │
│     │                │               │         │ acoustic) +0.5                                               │
├─────┼────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   2 │ Gym Hero       │ Max Pulse     │    4.37 │ genre match (pop) +3.0; energy 0.93 vs target 0.80 (+0.87);  │
│     │                │               │         │ acoustic preference match (non-acoustic) +0.5                │
├─────┼────────────────┼───────────────┼─────────┼──────────────────────────────────────────────────────────────┤
│   3 │ Rooftop Lights │ Indigo Parade │    2.46 │ mood match (happy) +1.0; energy 0.76 vs target 0.80 (+0.96); │
│     │                │               │         │ acoustic preference match (non-acoustic) +0.5                │
╰─────┴────────────────┴───────────────┴─────────┴──────────────────────────────────────────────────────────────╯

Mode: Energy-Similarity  [key='energy-similarity']

╭─────┬──────────────────┬───────────────┬─────────┬────────────────────────────────────╮
│   # │ Title            │ Artist        │   Score │ Reasons                            │
├─────┼──────────────────┼───────────────┼─────────┼────────────────────────────────────┤
│   1 │ Sunrise City     │ Neon Echo     │    3.92 │ energy 0.82 vs target 0.80 (+3.92) │
├─────┼──────────────────┼───────────────┼─────────┼────────────────────────────────────┤
│   2 │ Rooftop Lights   │ Indigo Parade │    3.84 │ energy 0.76 vs target 0.80 (+3.84) │
├─────┼──────────────────┼───────────────┼─────────┼────────────────────────────────────┤
│   3 │ Night Drive Loop │ Neon Echo     │    3.8  │ energy 0.75 vs target 0.80 (+3.80) │
╰─────┴──────────────────┴───────────────┴─────────┴────────────────────────────────────╯
```

**What the experiment reveals**

- **Balanced** → Sunrise City, Rooftop Lights, Gym Hero.
- **Genre-First** pushes **Gym Hero** (an exact pop match) up past Rooftop Lights (indie pop), because genre now outweighs mood.
- **Energy-Similarity** drops Gym Hero out of the Top-3 entirely and pulls in **Night Drive Loop**, whose energy (0.75) sits closest to the 0.80 target once genre and mood are ignored.

Same catalog, same listener — only the strategy changed. This makes the "weights are authorship" point concrete: the mode *is* the opinion.

---

## Limitations and Risks

- **Tiny catalog (18 songs).** Many profiles have only 1–2 matching songs available, so results can be shallow or repetitive.
- **Four features only.** The recommender ignores tempo and valence, so it can't distinguish two songs that match on genre/mood/energy/acoustic but differ musically elsewhere.
- **No understanding of lyrics, language, or audio** — it matches on pre-labeled attributes only.
- **Weighting can over-favor mood/genre**, as the adversarial experiment shows. A user's most explicit signal (a specific energy) can be overridden by category matches.
- **Single-value preferences.** One favorite genre and one favorite mood per user, whereas real listeners hold several at once.

I go deeper on these in the [Model Card](model_card.md).

---

## Reflection

Full reflection lives in the [**Model Card**](model_card.md) (Section 9).
In short: building this made clear that **weighting is authorship**: choosing mood (+2.0) over genre (+1.5) is a statement about what a good match *means*, not a neutral technical detail, and the adversarial experiment made that choice visible as a specific kind of "wrong." It also showed how soft the line is between "the algorithm" and "the data": half the surprising results came from the recipe and half from the tiny, uneven catalog. A recommender is less "smart" than *opinionated*: it inherits the taste of whoever set the weights and chose the songs.