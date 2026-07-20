# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted.

---

## Design Pattern (SF10) — Multiple Ranking Modes

**Which design pattern did you use?**

The **Strategy pattern**. Each ranking mode is a `ScoringStrategy` dataclass holding a set of weights (genre, mood, energy, acoustic). The scoring algorithm stays the same; swapping the strategy swaps the behavior. Modes are registered in a `SCORING_MODES` dictionary so new modes can be added without touching `score_song`.

**How did AI help you brainstorm or implement it?**

I described what I wanted — two or more interchangeable ranking modes a user could switch between — and asked the AI assistant how to keep it modular instead of writing an `if mode == "...":` chain inside the scoring function. It suggested extracting the weights into a small strategy object and selecting by name from a registry, and flagged the key constraint: keep the default ("balanced") weights identical to the original recipe so the existing pytest suite and prior output wouldn't change. It also caught that a mode which zeroes out a feature would otherwise print a misleading `+0.0` reason, so we guarded each rule to skip zero-weight features.

**How does the pattern appear in your final code?**

- `ScoringStrategy` dataclass and the `SCORING_MODES` registry in `src/recommender.py`.
- `score_song(user_prefs, song, strategy=None)` and `recommend_songs(..., strategy=None)` accept a strategy; `None` falls back to the balanced default.
- `experiment_ranking_modes()` in `src/main.py` runs the same profile through all three modes so a user can compare and switch.

**What did you verify manually?**

Confirmed the default (no-strategy) output is byte-for-byte identical to before the change, that the reconstructed sorted-by-score test still passes, and that the three modes produce genuinely different Top-3 rankings for the same listener (Genre-First promotes Gym Hero; Energy-Similarity pulls in Night Drive Loop).