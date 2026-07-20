# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**
A small content-based music recommender that matches a listener's stated taste profile against an 18-song catalog.

---

## 2. Intended Use

VibeFinder is a **classroom exploration project**, not a real product. Its purpose is to make the mechanics of a content-based recommender visible end-to-end: how song attributes and user preferences turn into a ranked list, and where the design choices produce visibly different behavior.

- **What it generates:**
A top-k ranked list of songs plus a plain-language reason for each recommendation
- **Who it's for:**
Learners studying how simple recommenders work, including how weighting choices, dataset size, and preference design shape the output.
- **Assumptions it makes about the user:**
That the user can articulate their taste as a single favorite genre, single favorite mood, target energy value, and YES/NO acoustic preference. In reality, listeners hold multiple simultaneous preferences that shift by context.
- **Not intended for:**
Real playlist generation, discovery beyond a tiny catalog, or any decision with real user impact.

---

## 3. How the Model Works

My recommender looks at four things about each song: its genre, mood, how energetic and how acoustic it is. The recommender then compares them to what a listener says they like. Genre and mood are simple YES/NO matches: the song either fits your favorite or not. Energy is judged by closeness: a song whose energy is near your target scores well, and the further away it is the less it scores. The system adds these up into a single number for each song, then sorts every song by that number and shows you the highest.

**Scoring recipe (in numbers):**

- Genre match: +1.5
- Mood match: +2.0 (weighted higher than genre because mood tracks the user's felt experience, which is what a "vibe" recommender is really trying to match)
- Energy closeness: up to +2.0, sliding down as the gap grows
- Acoustic preference match: +1.0

### Optional: Diversity / Artist Penalty (fairness feature)

The ranker supports an optional **artist penalty** (off by default). When enabled, each time a song is selected, any remaining song by an already-chosen artist has its effective score reduced, so the same artist cannot dominate the Top-5. This is a deliberate **fairness / anti-"filter-bubble"** measure: without it, a listener who matched strongly on one artist could have that artist crowd out otherwise-worthy songs by others. With the default High-Energy Pop profile, Neon Echo appears twice in the unpenalized Top-5 (*Sunrise City* #1, *Night Drive Loop* #4); enabling the penalty pushes the second Neon Echo track out in favor of *Concrete Bloom* by a different artist, giving every Top-5 slot a unique artist. Crucially, the #1 pick is unchanged — the penalty improves variety without weakening the strongest match. See the README "Diversity experiment" for the before/after tables.

### Ranking modes (Strategy pattern)

Scoring weights are bundled into interchangeable `ScoringStrategy` objects (a Strategy pattern) and selected from a `SCORING_MODES` registry: **Balanced** (the default recipe), **Genre-First** (exact-genre matches dominate), and **Energy-Similarity** (rank purely by energy closeness). The same listener produces a different ranking under each mode — e.g., Genre-First promotes "Gym Hero" above "Rooftop Lights," while Energy-Similarity drops "Gym Hero" out of the Top-3 in favor of "Night Drive Loop." This makes the model's central lesson concrete: the weighting *is* the opinion, and changing modes changes whose songs win. The default mode is unchanged, so all other results and the test suite are unaffected.

---

## 4. Data

The catalog starts as a CSV of songs, each described by attributes like genre, mood, energy, tempo, valence, danceability, and acousticness. The starter had 10 songs; I expanded it to 18 by adding songs across genres the starter lacked (hip-hop, punk, tango) and moods the starter was thin on (sad, angry). I deliberately included:

- Songs at both energy extremes (0.18 to 0.95) to stress-test the closeness formula.
- Two songs sharing an artist (Redline Riot) — and several other repeated artists (Neon Echo, Voltline, Paper Lanterns, LoRoom) — which the implemented diversity / artist-penalty feature acts on.
- Highly acoustic and non-acoustic tracks to exercise the acoustic bonus.

A limitation worth naming explicitly: this is a very small catalog that cannot represent the full range of musical taste (let alone music), and it only models one user at a time.

---

## 5. Strengths

- **Responsive to preferences.** 
Three deliberately diverse profiles (High-Energy Pop, Chill Acoustic, Hip-Hop Fan) each produce a completely different #1 recommendation: "Sunrise City", "Rain on Glass", and "Concrete Bloom", respectively. The system is genuinely sensitive to user input, not
returning generic results.

- **Design choices are visibly reflected in the ranking.**
Because I weighted mood (+2.0) above genre (+1.5), "Rooftop Lights" (indie pop, happy) consistently outranks "Gym Hero" (pop, intense) for the pop listener, even though the latter is the exact-genre match. This is not an accident; it's the recipe working as designed, and it makes the weight choices auditable in the output.

- **Every recommendation is explainable.**
Each ranked song carries a plain-language reason string listing which rules fired and how many points each contributed. This makes the system's behavior transparent in a way many production recommenders are not.

- **Graceful degradation.**
When a user's favorite genre has few songs in the catalog, the system falls back on partial matches (mood + energy + acoustic) rather than failing or returning nothing.

---

## 6. Limitations and Bias

- **Sparse-genre falloff.**
When a user's favorite genre has few songs the catalog (e.g., only two hip-hop songs in 18), the top-5 quickly fills with cross-genre songs that satisfy the other three rules. The recommender degrades gracefully rather than failing, but a hip-hop fan may still see mostly non-hip-hop songs, which in a real product would look like the system "ignoring" their genre.

- **Category matches dominate numeric closeness by design.**
My recipe awards up to +4.5 for category matches (genre + mood + acoustic) but caps energy at +2.0. A user requesting a *specific* energy but with *general* genre/mood tastes may get recommendations that ignore their most explicit signal, as seen in the adversarial experiment, where a "low-energy pop" request still returned "Sunrise City" (energy 0.82) at #1 because genre + mood + acoustic all matched.

- **The acoustic bonus is symmetric and probably shouldn't be.**
The +1.0 acoustic bonus fires when the song matches the user's `likes_acoustic` preference, including when the user answered `False`. This inflates scores across the board for the majority of users (who don't specifically want acoustic) and gives no meaningful signal. The bonus should probably only apply when `likes_acoustic=True`.

- **Small catalog, thin diversity.**
18 songs across aprox 10 genres means  many taste profiles have only 1–2 matching songs available. This isn't a scoring bug, but a data limitation that would resolve with a larger, more balanced catalog.

- **Single-value preferences.**
The user profile stores one favorite genre and one favorite mood. Real listeners like multiple genres and shift moods over time.

---

## 7. Evaluation

**Profiles tested.**
Three deliberately diverse listener profiles were run against the 18-song catalog: a High-Energy Pop listener (default), a Chill Acoustic listener (low energy, sad, wants acoustic), and a Hip-Hop Fan (intense, high energy). A fourth adversarial profile (happy pop but low energy) was added to stress-test conflicting preferences.

**What I looked for.**
Whether each profile's #1 differed (proving responsiveness to preferences), whether the ranking order matched my own musical intuition, and where the recommender fell back on partial matches when perfect matches were scarce.

**What surprised me.**
Two things:
1) How visible my weight choices became in the output. "Rooftop Lights" consistently beat "Gym Hero" for the pop listener, purely because I weighted mood above genre.
2) How the adversarial profile exposed a real tension: my recipe treats category matches as more important than numeric closeness, which is defensible in general but produces obviously "wrong" results when a user asks for something specific like low energy and gets a high-energy song back because everything else matched.

**Comparison across profiles.**
The Chill Acoustic profile shifts the top results toward low-energy acoustic tracks ("Rain on Glass", "Empty Apartment") that the pop profile ignores entirely. The Hip-Hop profile surfaces intense high-energy tracks from multiple genres because only one hip-hop song satisfies all four criteria. Each profile "sees" a different slice of the catalog, which is exactly what a working content-based recommender should do.

---

## 8. Future Work

- **Ranked preferences instead of single favorites.**
Let users name an ordered list of favorite genres (jazz #1, indie #2, hip-hop #3). Scoring becomes graded: full points for the top match, partial points for lower-ranked matches. Richer signal than a binary "match or nothing."

- **Stated vs revealed preference.**
What a user *says* they like often disagrees with what they *actually stream*. A future version could observe listening behavior over time and calibrate the weight of each self-reported preference against the user's actual behavior, down-weighting stated preferences that behavior contradicts. This is the argument for hybrid recommenders that combine content-based signals (what you say and what songs are) with collaborative signals (what you actually do).

- **Asymmetric acoustic bonus.** Only award the +1.0 when `likes_acoustic=True`, so the majority of users don't get inflated scores from a preference they didn't express.

- **Extend the diversity penalty to genre.**
The artist penalty is implemented (see Section 3). A natural next step is to also penalize songs sharing a *genre* with songs already in the Top results, to prevent one genre (not just one artist) from dominating (e.g., the Chill Acoustic result leans heavily on acoustic/lofi tracks).

- **Add valence back in.**
I deliberately set aside valence (happy-vs-sad measure) in v1 to keep the recipe focused. Adding it would let the system distinguish between "happy" and "sad" songs beyond the mood label alone, since mood is a coarse categorical while valence is a smooth numeric.

- **Contextual weights.**
Let weights shift based on context. If the user asks for a specific energy (e.g., 0.2), treat energy as a *hard* constraint rather than a soft slide, so an energy-perfect song can outrank a triple-category-match with wildly wrong energy.

---

## 9. Personal Reflection

Building this recommender made two things cleared:

First, **weighting is authorship.** The choice to make mood +2.0 versus genre +1.5 is not a technical detail, but a statement of what matters most in matching a listener to a song, at least at this basic level. The adversarial experiment made this visible: my recipe produces a particular kind of "wrong" that reflects set priorities. A different weighting would produce a different "wrong". Real recommender teams are, in effect, deciding *for millions of people* what counts as a good match, and *how* to match.

Second, **the boundary between "the algorithm" and "the data" is soft.** Half the surprises in this project came from the recipe (weights, closeness formula, acoustic bonus) and half came from the catalog, however tiny (thin hip-hop coverage, repeated artists, energy distribution). Neither works without the other. When (say) Spotify recommends something odd, it might be the algorithm per se or it might be that their data about that user (or that genre) is thinner than I'd expect.

As such, one can think that recommendation apps less as "smart" and more as "opinionated": they have something akin to taste, set by the humans who chose the weights.