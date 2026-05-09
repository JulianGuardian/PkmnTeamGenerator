# Pokémon Team Maker — Project Summary

## Libraries used

| Library | Purpose |
|---|---|
| **FastAPI** | Web framework that exposes the REST API. Handles routing, request/response lifecycle, and automatic documentation at `/docs`. |
| **Uvicorn** | ASGI server that runs the FastAPI application. |
| **Pydantic** | Data validation and serialization. Used to define the response schemas (`PokemonSchema`, `MoveSchema`, `ProfileSchema`, etc.) and guarantee the JSON output is well-formed. |
| **Requests** | HTTP client used to call the PokéAPI during dataset construction. |
| **json** | Standard library module used to read and write the local dataset files. |
| **os** | Standard library module used to check file existence and build file paths. |
| **random** | Standard library module used in the genetic algorithm for team initialization, mutation, and selection. |
| **collections.Counter** | Used to count role occurrences, type frequencies, and shared weaknesses within a team. |

---

## APIs used

### PokéAPI — `https://pokeapi.co/api/v2`

Free, open, read-only REST API with data for every Pokémon game. No authentication required.

The app calls three endpoints during dataset construction:

| Endpoint | Used for |
|---|---|
| `GET /pokemon?limit=1025` | Fetch the list of all Pokémon names |
| `GET /pokemon/{name}` | Fetch types, base stats, learnset, ability, and sprite for each Pokémon |
| `GET /pokemon-species/{name}` | Fetch whether a Pokémon is legendary or mythical |
| `GET /move/{name}` | Fetch all mechanical data for each move (power, accuracy, effects, stat changes, etc.) |
| `GET /ability/{name}` | Fetch the English description of a Pokémon's ability |

After the datasets are saved locally, the API is only called again when a team is generated — once per Pokémon to fetch the ability description (since that field is not stored in the dataset).

---

## How the backend works — simple summary

1. **Server starts** → checks if the two dataset files exist. If not, downloads ~1025 Pokémon and ~950 moves from PokéAPI and saves them as JSON. This only happens once.

2. **User hits `GET /team`** → the backend runs a genetic algorithm over the Pokémon dataset to find a team of 6 that scores well on type coverage, role diversity, and stat balance.

3. **For each Pokémon in the team**, the backend:
   - Fetches its full data (ability, sprite, full learnset) from PokéAPI or local cache.
   - Assigns it a competitive role based on its stats.
   - Selects 4 moves from the moves dataset, filtering out bad moves and scoring the rest.

4. **Returns a JSON response** with all 6 Pokémon fully described: types, stats, ability (with description), 4 moves (with descriptions), and a profile with the role and a written explanation.

---

## What machine learning is used?

The app uses a **genetic algorithm**, which sits in a grey area depending on context:

- **Strictly speaking** (academic definition): genetic algorithms belong to **evolutionary computation**, a subfield of AI but *not* of Machine Learning. ML refers specifically to systems that learn a model from data — the genetic algorithm has no training data, no learnable weights, and nothing that persists between runs.
- **Broadly speaking** (industry / practical use): many curricula and job descriptions group genetic algorithms under "AI/ML" because they find optimal solutions without being explicitly programmed. Calling it AI is accurate; calling it ML is a simplification.

**The precise answer for this project: it uses AI-based optimization (evolutionary computation), not machine learning.**

Comparison with traditional ML:

| | Genetic Algorithm (this app) | Traditional ML |
|---|---|---|
| Requires training data | No | Yes |
| Has learnable weights | No | Yes |
| Improves over time | Yes, within a single run | Yes, across training epochs |
| Is deterministic | No (random mutations) | Depends |
| Generalizes to new inputs | No | Yes |

### What the genetic algorithm does here

It treats each candidate team of 6 Pokémon as an **individual** in a population. In each **generation**:

- The **20 candidate teams** are scored by a **fitness function** that measures type coverage, role diversity, defensive synergy, and stat balance.
- The **top 5 teams survive** unchanged (elitism).
- **15 new teams** are created by taking a parent from the top 10 and randomly replacing one Pokémon (mutation).
- After **20 generations**, the highest-scoring team is returned.

The fitness function is entirely hand-crafted based on competitive Pokémon knowledge — it is not learned from data. The scoring rules (e.g. "+300 per type covered", "−800 per shared weakness with 4+ members") were designed manually to reflect what makes a team strong.

### What could be added with real ML

If the project were extended with machine learning, possible approaches include:

- **Reinforcement learning** — train an agent to build teams by simulating battles and rewarding wins.
- **Neural fitness function** — replace the hand-crafted scoring with a model trained on competitive team data (e.g. from Pokémon Showdown replays).
- **Move recommendation model** — learn which moves are most effective for each Pokémon based on usage statistics from competitive play.
