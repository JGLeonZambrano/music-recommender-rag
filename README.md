# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Explain your design in plain language.

Some prompts to answer:

- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo
- What information does your `UserProfile` store
- How does your `Recommender` compute a score for each song
- How do you choose which songs to recommend

You can include a simple diagram or bullet list if helpful.

## How The System Works

This project is a **content-based** music recommender. It looks at the
attributes of each song and matches them against a single user's stated
taste. In other words: "this song is *like* the songs you already like."

This is different from **collaborative filtering**, the approach behind apps
like Spotify's Discover Weekly, which ignores song attributes and instead
looks at the behavior of a *crowd*: "people who listen to what you listen
to also loved this." Collaborative filtering isn't just unused here, it's
impossible: I only have data for one user and no record of any crowd's
listening behavior, so I must match on song attributes instead.

Every content-based recommender works in three stages:

1. **Input data** — objective facts about each song (its columns in
   `songs.csv`: genre, mood, energy, etc.).
2. **User preferences** — what *this* listener wants, stored as a taste
   profile (e.g. favorite genre, favorite mood, target energy).
3. **Ranking / selection** — the logic that scores each song against the
   user's preferences and sorts them to pick the best few.

### Features my system uses

My `Song` objects carry several attributes, but my recommender scores on
**four** of them:

- **genre** (category) — does the song's genre match the user's favorite?
- **mood** (category) — does the song's mood match the user's favorite?
- **energy** (numeric, 0.0–1.0) — how *close* is the song's energy to the
  user's target?
- **acousticness** (numeric, 0.0–1.0) — folded in via the user's
  `likes_acoustic` preference.

I deliberately left out two available columns: **tempo_bpm**, because it
overlaps heavily with energy (fast songs tend to feel energetic) and would
double-count the same "vibe"; and **valence** (a song's happy-vs-sad
measure), which I set aside to keep the first version focused and may add
later.

My `UserProfile` stores: favorite_genre, favorite_mood, target_energy, and
likes_acoustic.

<!-- TODO: Add the scoring recipe here once weights are decided (Phase 1 Step 3). -->


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

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

```
# e.g.:
# User profile: genre=indie, mood=chill, energy=low
# Recommendations:
#   1. ...
#   2. ...
#   3. ...
```

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



