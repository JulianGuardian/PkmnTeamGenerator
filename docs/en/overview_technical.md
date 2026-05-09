# Pokémon Team Maker — Intermediate / Advanced Technical Overview

## Architecture

```
app/
├── api/
│   └── routes.py              # FastAPI router, startup event, /team endpoint
├── application/
│   ├── team_generator.py      # Genetic algorithm — selects 6 Pokémon
│   ├── team_evaluator.py      # Fitness function — scores a candidate team
│   ├── role_assigner.py       # Assigns a competitive role from stats
│   ├── moveset_generator.py   # Selects 4 moves per Pokémon
│   └── type_coverage.py       # Type effectiveness engine
├── domain/
│   ├── models.py              # Pokemon dataclass
│   └── evaluator.py           # Role descriptions and explain_pokemon()
├── infraestructure/
│   └── pokeapi_client.py      # Dataset download, caching, full Pokémon fetch
└── schemas/
    └── pokemon_schema.py      # Pydantic response models
```

---

## Data Layer

### Dataset construction (`pokeapi_client.py`)

Two datasets are built on first run and persisted as JSON:

**`pokemon_dataset.json`** — lightweight record per Pokémon:
```json
{ "name": "garchomp", "types": ["dragon","ground"], "stats": {...}, "is_legendary": false }
```

**`moves_dataset.json`** — rich record per move:
```json
{
  "name": "earthquake", "type": "ground", "damage_class": "physical",
  "power": 100, "accuracy": 100, "priority": 0, "pp": 10,
  "target": "all-other-pokemon",
  "recoil": 0, "drain": 0, "healing": 0,
  "ailment": "none", "ailment_chance": 0, "flinch_chance": 0,
  "stat_chance": 0, "crit_rate": 0, "min_hits": null, "max_hits": null,
  "effect_short": "...", "description": "...", "meta_category": "damage",
  "min_turns": null, "max_turns": null,
  "user_stat_drops": {}, "user_stat_boosts": {}, "enemy_stat_drops": {}
}
```

#### Stat change classification logic

The API's `stat_changes` array doesn't explicitly say whether a change affects the user or the opponent. The client reconstructs this from three fields: `target_name`, `damage_class`, and `stat_chance`:

```
change > 0 AND target == "user"                     → user_stat_boosts   (Swords Dance)
change < 0 AND damage_class == "status"
    AND target in rivals                             → enemy_stat_drops   (Charm, Screech)
    AND target == "user"                             → user_stat_drops    (Clangorous Soul)
change < 0 AND damage_class != "status"
    AND 0 < stat_chance < 100                        → enemy_stat_drops   (Crunch 20%)
    AND stat_chance == 100 OR stat_chance == 0       → user_stat_drops    (Close Combat, Leaf Storm)
```

The key insight: `stat_chance == 100` on an offensive move means a guaranteed self-penalty (Close Combat), not a secondary effect on the opponent.

---

## Type Engine (`type_coverage.py`)

Loaded from `data/type_chart.json` — a pre-built lookup table with `strengths`, `weaknesses`, and `immunes` per type.

Core functions:

| Function | Description |
|---|---|
| `type_effectiveness(atk, def_types)` | Returns the damage multiplier (0, 0.25, 0.5, 1, 2, 4) |
| `offensive_coverage(types)` | Set of types hit super-effectively by a Pokémon's STAB |
| `move_coverage(move_type)` | Set of types hit super-effectively by one move |
| `pokemon_weaknesses(types)` | All types dealing ≥2x to this Pokémon |
| `pokemon_resistances(types)` | All types dealing ≤0.5x |
| `team_offensive_coverage(team)` | Union of offensive coverage across all 6 members |
| `team_defensive_weaknesses(team)` | Counter of how many members share each weakness |
| `type_synergy_score(team)` | +50 per pair where one member resists another's weakness |

---

## Genetic Algorithm (`team_generator.py`)

### Population and selection

```python
population = [random_team() for _ in range(20)]  # 20 random teams

for generation in range(20):
    population.sort(key=fitness, reverse=True)
    next_gen = population[:5]                     # elitism: keep top 5

    while len(next_gen) < 20:
        parent = random.choice(population[:10])   # tournament from top 10
        child = mutate(parent)                    # replace 1 random Pokémon
        next_gen.append(child)

    population = next_gen
```

### Mutation constraints

- No duplicate Pokémon names in the team.
- If the team already has 1 legendary, the mutated slot must be non-legendary.

### Fitness function (`team_evaluator.py`)

```
score = 0

+ len(types covered super-effectively) × 300
+ 2000 if ≥15 types covered, +1000 if ≥12

- count × 800 for any type weakness shared by ≥4 members
- count × 300 for ≥3 members sharing a weakness
- count × 50  for 2 members sharing a weakness

+ type_synergy_score(team)           # pair-wise resistance coverage

- (count - 2) × 500 for each type appearing ≥3 times

+ 400 if ≥2 physical attackers (atk > 100)
+ 400 if ≥2 special attackers (spa > 100)
+ 500 if at least 1 of each (mixed offense)
+ 300 if ≥2 fast members (speed > 100)
+ 300 if ≥1 bulky member (HP × (def+spd)/2 > 14000)
```

Additionally, `role_diversity_bonus()` adds ±1000/±10000 based on role presence:

```python
required = ["annoyer", "revenge_killer", "physical_sweeper", "special_sweeper"]
# +1000 per role present, -10000 per role missing
# +1000 if tank >= 2 OR (tank >= 1 AND balanced >= 1), else -10000
```

### Hard constraints (`meets_role_requirements`)

After evolution, the winning team must satisfy all of these or the algorithm falls back to brute-force random sampling (up to 1000 attempts):

- All 4 required roles present
- At least 1 tank or balanced
- No primary type appears 3+ times
- Offensive coverage ≥ 10 types

---

## Role Assignment (`role_assigner.py`)

Pure stat-based classification. Applied to both the dataset Pokémon (dict) and full Pokémon objects:

```python
bulk = hp * (defense + special_defense) / 2

is_wall = bulk > 18000 OR (defense > 130 AND sp_def > 100 AND speed < 60)
if is_wall AND speed < 80  → "annoyer"
elif speed > 120           → "revenge_killer"
elif attack > 120          → "physical_sweeper"
elif sp_attack > 120       → "special_sweeper"
elif bulk > 15000          → "tank"
else                       → "balanced"
```

---

## Moveset Generator (`moveset_generator.py`)

### Filtering pipeline

Each move passes through a sequential filter:

1. Must be in the Pokémon's learnset
2. Not in `BANNED_MOVES` or `LOW_QUALITY_MOVES`
3. Target not in `DOUBLES_ONLY_TARGETS`
4. `recoil` not ≤ −33 (heavy recoil), not ≤ −100 (faint)
5. `is_charge_move`: `effect_short` must not contain "recharge", "next turn", or "second turn"
6. `is_lockin_move`: `min_turns ≥ 2` OR `"confused after"` in `effect_short`
7. `self_debuffs_main_attack`: `user_stat_drops` on attack/sp_attack ≤ −2
8. `rest`: only allowed if `HP × (def + sp_def) / 2 ≥ 12000`
9. `accuracy` ≥ 70
10. `trick-room`: only if team average speed ≤ 90
11. Dominant damage class: if `|attack − sp_attack| > 20`, filter moves of the opposite class
12. Stat floor: physical moves filtered if `attack < 40`; special if `sp_attack < 40`

### Preferred damage class

```python
diff = pokemon.attack - pokemon.sp_attack
if diff > 20  → "physical"
if diff < -20 → "special"
else          → None  (mixed)
```

### Scoring (`score_move`)

Each valid move is assigned a competitive score:

```
base_score = power + (accuracy − 70) × 0.5
           − (50 − power) × 2  if power < 50  (low-power penalty)

+ 30     if STAB
+ 80 × n if move covers n types the rest of the team doesn't
+ 50/25  if priority ≥ 2 / == 1
+ 20 × crit_rate
+ ailment_chance × 0.3 + flinch_chance × 0.2 + stat_chance × 0.2
+ 20     if drain move
+ sum(|enemy_stat_drops|) × 15
+ 20 + total_user_boosts × 8  if setup move
+ 35     if recovery move
+ 40     if pivot move (U-turn, Volt Switch, etc.)
+ UTILITY_BONUS[name]  (stealth-rock=50, defog=50, taunt=50, knock-off=40…)
+ META_BONUS[name]     (earthquake=40, ice-beam=35, moonblast=35…)
```

### Role-based move selection (`pick_role_moves`)

After scoring, each role has a specific template:

| Role | Slot 1 | Slot 2 | Slot 3 | Slot 4 |
|---|---|---|---|---|
| physical_sweeper | Best STAB | 2nd best STAB | Best coverage | Physical setup (or more coverage) |
| special_sweeper | Best STAB | 2nd best STAB | Best coverage | Special setup (or more coverage) |
| revenge_killer | Priority move | Best STAB | 2nd STAB | Pivot / coverage |
| annoyer | Opponent debuff | Status ailment | Defensive setup | Recovery |
| tank | Best STAB | Drain move | Defensive setup | Recovery |
| balanced | Best STAB | Best coverage | Setup (by dominant stat) | Utility |

After role-based selection, `complete_moveset()` fills remaining slots greedily by score, prioritizing type coverage and avoiding duplicate move types.

A final guarantee ensures at least 1 damaging move is always present.

### Coverage awareness

Each Pokémon's moveset is computed with knowledge of what the rest of the team already covers:

```python
team_covered    = union of offensive_coverage(p.types) for all teammates
uncovered_types = ALL_18_TYPES − team_covered
```

Coverage moves scoring gets `+80 × (types newly covered)`, driving the algorithm toward filling gaps rather than duplicating what teammates already handle.

---

## Response Schema

```
PokemonSchema
├── name: str
├── sprite: str (URL)
├── types: List[str]
├── ability: str
├── ability_description: str | null
├── stats: StatsSchema {hp, attack, defense, sp_attack, sp_defense, speed}
├── moves: List[MoveSchema]
│   └── MoveSchema
│       ├── name: str
│       ├── type: str
│       ├── damage_class: str | null       ("physical", "special", "status")
│       ├── power: int | null              (null for status moves)
│       ├── accuracy: int | null           (null for moves that never miss)
│       ├── pp: int | null
│       └── description: str | null
└── profile: ProfileSchema
    ├── role: str
    └── role_description: str
```
