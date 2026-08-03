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
---

## Agentic Workflow (P4 Stretch) — Self-Critique and Revise Loop

**Which agentic pattern did I use?**

A **critic-and-reviser loop** with a decision point. After the pipeline generates its first draft of commentary, a second Gemini call reviews that draft against the user's query and the selected picks, returns structured JSON with three fields (`on_topic`, `grounded`, `concerns`), and the pipeline decides whether to accept the draft as-is or send it back for revision. If the critic flags issues, a third Gemini call rewrites the commentary addressing the flagged concerns; if not, the draft is kept. Every stage of this loop is recorded in the `trace["stages"]` list on the `RagResult` object so the decision chain is inspectable after the fact.

**Where the pattern lives in the code.**

- `CRITIC_PROMPT` and `REVISER_PROMPT` in `src/rag_pipeline.py` define the two agent roles.
- The `recommend()` function in `src/rag_pipeline.py` orchestrates the loop, adding stages `llm_commentary_v1`, `llm_self_critique`, and either `llm_commentary_v2` (if revision was applied) or `llm_commentary_accepted` (if the critic approved the draft) to the trace.
- The trace field `revision_applied` (bool) records the final decision at the top level of the trace dict.

**How AI helped me implement it.**

I described what I wanted: a stage between commentary generation and Guardrail 3 where the LLM would review its own draft and either accept or rewrite. Claude proposed the specific shape: two separate prompts (critic asks for structured JSON only, reviser gets the concerns list and rewrites), and a JSON extraction step in Python that tolerates whitespace or code fences the model might add around the JSON. Claude also flagged the risk that doubling or tripling the number of LLM calls per query would multiply the chance of hitting a Gemini 503, and pointed at the existing three-tier fallback in `src/llm_client.py` as sufficient mitigation. That prediction turned out to be correct: the first live run captured multiple `[llm_client] gemini-3.6-flash failed: ClientError` lines from the extra critic and reviser calls, and the fallback layer handled all of them.

**Where the intermediate reasoning is saved.**

Runtime reasoning traces from the agentic loop are captured in the pipeline's output log:
- `assets/demo_pipeline_output.txt` shows the `Self-critique:` line (with the parsed JSON verdict: `on_topic`, `grounded`, `concerns`) and the `Action:` line (either `commentary ACCEPTED without revision` or `commentary REVISED after critique`) for every real query.

At the API level, the full `trace["stages"]` list on each `RagResult` contains:
- `llm_commentary_v1` — the initial draft with its full text
- `llm_self_critique` — the critic's raw response (truncated to 400 chars) and the parsed JSON verdict
- `llm_commentary_v2` (only if revision fired) — the reviser's output with the concerns that prompted it, OR
- `llm_commentary_accepted` (only if the critic approved v1) — a note recording the acceptance

Together, these give a complete audit trail of why each user-facing commentary looks the way it does.

**What I verified manually.**

- Both real queries in the smoke test triggered the critic and the critic returned parseable JSON in every case.
- The critic self-approved both drafts in the first run (`concerns=[]`), which is the expected majority behavior: the commentary prompt already constrains output tightly enough that most drafts pass the critic's grounded/on-topic checks.
- Confirmed that when Gemini 503s hit the critic call, the fallback to `gemini-3.5-flash-lite` returned valid JSON and the loop continued unaffected.
- Confirmed the loop adds no failure modes: if the critic response is unparseable, the pipeline treats it as "critic could not verify" and keeps the draft rather than crashing.

**Why this counts as an agentic workflow and not just an extra LLM call.**

Three things distinguish this from a linear chain:
1. **A decision point.** The pipeline actively branches based on the critic's structured output. Different queries route through different downstream stages.
2. **Role separation.** The critic and reviser use different prompts and are aware of each other's outputs: the reviser sees both the picks and the specific concerns the critic raised.
3. **Auditable reasoning.** Every stage is logged with its role, its input, and its output, so a reader can reconstruct the full decision chain after the fact.

---

## Fine-Tuning or Specialization (P4 Stretch) — Persona-Constrained Commentary

**Which specialization pattern did I use?**

**Constrained tone and style via few-shot prompting.** Not fine-tuning. `src/personas.py` defines a persona dict with a system prompt (the "Record Store Clerk" voice with explicit rules: fragments allowed, exclamations banned, no cliches, references the room not the emotion) and a one-shot example showing correct output for a different query. `scripts/persona_comparison.py` runs the same picks through both the baseline commentary prompt and the persona-constrained prompt.

**Where the pattern lives in the code.**

- `src/personas.py`: the `PERSONA_CLERK` dict and the `generate_persona_commentary()` function.
- `scripts/persona_comparison.py`: the driver script that runs both voices on three queries and reports numerical metrics.
- `assets/persona_comparison.txt`: the captured comparison output cited in model card Section 16.

**What the intermediate reasoning looks like.**

Every run of `scripts/persona_comparison.py` prints both the baseline and specialized commentary side by side for each query, plus per-query metrics (character count, average sentence length, exclamation count, banned-cliche count), plus an aggregate summary. This gives a full audit trail of how the specialization altered each individual output, not just the aggregate. See `assets/persona_comparison.txt`.

**What I verified manually.**

- The persona system prompt actually constrains the output (sentence length halved, cliches dropped to zero).
- The comparison is fair: same picks, same query, only the prompt changes.
- The specialized voice sometimes volunteers unverifiable auditory claims ("Taylor steel-string with a cracked bridge"), which is a real limitation documented in model card Section 16. Style change and factuality are related.
- Guardrail 3 still runs on persona-generated commentary in the pipeline (though the comparison script bypasses the pipeline to isolate the voice change).
