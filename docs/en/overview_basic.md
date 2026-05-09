# Pokémon Team Maker — Basic / Intermediate Overview

## What does the app do?

It generates a competitive team of 6 Pokémon, each with 4 moves, that work well together. The team is designed to cover a wide variety of types both offensively and defensively, and to include a diverse set of battle roles.

---

## Where does the data come from?

The app downloads data from **PokéAPI**, a free public API that contains information about every Pokémon and move in the games.

Two JSON files are saved locally to avoid re-downloading every time:

| File | Contents |
|---|---|
| `data/pokemon_dataset.json` | Name, types, stats, and legendary status for ~1025 Pokémon |
| `data/moves_dataset.json` | Name, type, power, accuracy, effects, and mechanics for ~950 moves |

If these files already exist, the app uses them directly. If not, it downloads everything from the API automatically when the server starts.

---

## How is the team built?

The team is built in two stages:

### Stage 1 — Choose the 6 Pokémon

The app uses a **genetic algorithm** — an optimization technique inspired by natural selection — to find the best combination of 6 Pokémon.

It works like this:

1. **Create a random population** of 20 candidate teams.
2. **Score each team** based on how good it is (type coverage, role diversity, stat balance).
3. **Keep the 5 best teams** and generate 15 new ones by slightly mutating (changing one Pokémon) from the top 10.
4. **Repeat for 20 generations.**
5. **Return the best team** found across all generations.

Teams are scored on things like:
- How many of the 18 types they can hit super-effectively
- How many different battle roles are represented
- Whether multiple Pokémon share the same type weakness

### Stage 2 — Assign 4 moves to each Pokémon

Once the 6 Pokémon are selected, each one is assigned a **role** based on its stats:

| Role | Description |
|---|---|
| `physical_sweeper` | High physical attack — focuses on dealing damage |
| `special_sweeper` | High special attack — focuses on dealing damage |
| `revenge_killer` | Very fast — comes in to finish off weakened opponents |
| `annoyer` | High bulk — uses status moves to wear down opponents |
| `tank` | High bulk — absorbs hits and deals sustained damage |
| `balanced` | No extreme stats — flexible, versatile profile |

Then the app selects 4 moves for each Pokémon using the following criteria:

- **STAB moves** (same type as the Pokémon) for reliable damage
- **Coverage moves** that hit types the rest of the team can't cover
- **Setup moves** appropriate for the Pokémon's role (e.g. Swords Dance for physical sweepers)
- **Recovery, status, or utility moves** for annoyers and tanks

Bad or situational moves are filtered out — things like two-turn moves (Solar Beam), self-KO moves (Explosion), moves with very low accuracy, or moves that are only useful in doubles battles.

---

## How is the result returned?

The app exposes a single REST endpoint:

```
GET /team
```

It returns a JSON object with 6 Pokémon. Each one includes:

- Name, sprite URL, types
- Ability name and description
- Stats (HP, Attack, Defense, Sp. Atk, Sp. Def, Speed)
- 4 moves, each with name, type, and description
- A `profile` object with the assigned role and a written explanation of why

---

## Rules and constraints

- **Maximum 1 legendary** per team (optional — the team may have zero).
- **Minimum BST of 450** — very weak Pokémon are excluded.
- **No more than 2 Pokémon** sharing the same primary type.
- **Must cover at least 10 of the 18 types** offensively.
- **Must have all 4 required roles**: physical sweeper, special sweeper, revenge killer, and annoyer, plus at least one tank or balanced.

---

## Summary flow

```
Server starts
    │
    ▼
Load / download datasets
    │
    ▼
GET /team request received
    │
    ▼
Genetic algorithm selects 6 Pokémon
    │
    ▼
Each Pokémon gets a role assigned
    │
    ▼
Each Pokémon gets 4 moves selected
    │
    ▼
JSON response returned
```
