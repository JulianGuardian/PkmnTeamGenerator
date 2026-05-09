# Pokémon Team Maker

A REST API that generates competitive Pokémon teams of 6 members, each with 4 moves, using a genetic algorithm and data from PokéAPI.

## How it works

1. The app loads Pokémon and move data from two JSON datasets included in the repository. If the files are missing it downloads them from [PokéAPI](https://pokeapi.co) automatically.
2. When a team is requested, a genetic algorithm evolves a population of candidate teams over 20 generations, scoring each one on type coverage, role diversity, and defensive synergy.
3. Each Pokémon in the final team is assigned a competitive role and 4 moves selected and scored by a rule-based engine.

For a detailed explanation see [`docs/`](docs/).

## Requirements

- Python 3.10+

## Setup

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

## Running

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs at `http://localhost:8000/docs`.

## Endpoint

### `GET /team`

Generates and returns a competitive team of 6 Pokémon.

**Response example:**
```json
{
  "team": [
    {
      "name": "garchomp",
      "sprite": "https://raw.githubusercontent.com/PokeAPI/sprites/...",
      "types": ["dragon", "ground"],
      "ability": "rough-skin",
      "ability_description": "Inflicts damage on the attacker on contact.",
      "stats": {
        "hp": 108, "attack": 130, "defense": 95,
        "sp_attack": 80, "sp_defense": 85, "speed": 102
      },
      "moves": [
        { "name": "earthquake",  "type": "ground", "damage_class": "physical", "power": 100, "accuracy": 100, "pp": 10, "description": "..." },
        { "name": "dragon-claw", "type": "dragon", "damage_class": "physical", "power": 80,  "accuracy": 100, "pp": 15, "description": "..." },
        { "name": "swords-dance","type": "normal", "damage_class": "status",   "power": null, "accuracy": null, "pp": 20, "description": "..." },
        { "name": "stone-edge",  "type": "rock",   "damage_class": "physical", "power": 100, "accuracy": 80,  "pp": 5,  "description": "..." }
      ],
      "profile": {
        "role": "physical_sweeper",
        "role_description": "Physical attack specialist. Notable stats: very high physical attack, good speed."
      }
    }
  ]
}
```

## Team guarantees

| Rule | Value |
|---|---|
| Team size | Always 6 |
| Legendary Pokémon | 0 or 1 maximum |
| Minimum BST | 450 |
| Offensive type coverage | At least 10 of 18 types |
| Max same primary type | 2 Pokémon |
| Roles always present | Physical sweeper, special sweeper, revenge killer, annoyer, + tank or balanced |

## Project structure

```
app/
├── api/routes.py                 # Endpoint definitions
├── application/
│   ├── team_generator.py         # Genetic algorithm
│   ├── team_evaluator.py         # Fitness function
│   ├── role_assigner.py          # Role assignment from stats
│   ├── moveset_generator.py      # Move filtering and selection
│   └── type_coverage.py          # Type effectiveness engine
├── domain/
│   ├── models.py                 # Pokemon model
│   └── evaluator.py              # Role descriptions
├── infraestructure/
│   └── pokeapi_client.py         # API calls and dataset management
└── schemas/
    └── pokemon_schema.py         # Pydantic response models
data/
├── type_chart.json               # Type effectiveness lookup table
├── pokemon_dataset.json          # Auto-generated on first run
└── moves_dataset.json            # Auto-generated on first run
docs/
├── en/
│   ├── overview_basic.md         # Basic / intermediate explanation
│   ├── overview_technical.md     # Technical deep-dive
│   └── project_summary.md        # Libraries, API, ML discussion
└── es/
    ├── resumen_basico.md          # Explicación básica / intermedia
    ├── resumen_tecnico.md         # Análisis técnico detallado
    └── resumen_proyecto.md        # Librerías, API, discusión ML
```

## Tech stack

| | |
|---|---|
| Framework | FastAPI |
| Server | Uvicorn |
| Validation | Pydantic |
| Data source | PokéAPI |
| Optimization | Genetic algorithm (evolutionary computation) |
| Language | Python 3.10+ |
