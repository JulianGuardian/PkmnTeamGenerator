import json
import os

import requests

from app.domain.models import Pokemon

BASE = "https://pokeapi.co/api/v2"
DATA_PATH = "data/pokemon_dataset.json"
MOVES_PATH = "data/moves_dataset.json"

cache = {}
moves_cache = {}


# -----------------------------
# POKEMON DATASET
# -----------------------------
def get_all_pokemon_names():
    url = f"{BASE}/pokemon?limit=1025&offset=0"
    data = requests.get(url, timeout=10).json()
    return [p["name"] for p in data["results"]]


def load_pokemon_dataset(limit=1025):
    names = get_all_pokemon_names()[:limit]
    dataset = []

    for i, name in enumerate(names, start=1):
        try:
            p = requests.get(f"{BASE}/pokemon/{name}", timeout=10).json()
            print(f"Downloading Pokemon {i}/{limit}: {name}")

            species = requests.get(f"{BASE}/pokemon-species/{name}", timeout=10).json()

            dataset.append(
                {
                    "name": name,
                    "types": [t["type"]["name"] for t in p["types"]],
                    "stats": {
                        stat["stat"]["name"]: stat["base_stat"] for stat in p["stats"]
                    },
                    "is_legendary": species.get("is_legendary", False),
                }
            )
        except Exception:
            continue

    return dataset


def load_or_create_dataset(limit=1025):
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r") as f:
            return json.load(f)

    dataset = load_pokemon_dataset(limit)

    os.makedirs("data", exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(dataset, f)

    return dataset


# -----------------------------
# MOVES DATASET
# -----------------------------
def get_all_moves(limit=950):
    url = f"{BASE}/move?limit={limit}"
    data = requests.get(url, timeout=10).json()
    return [m["name"] for m in data["results"]]


def load_moves_dataset(limit=950):
    move_names = get_all_moves(limit)
    dataset = []

    print("\nDownloading moves...\n")

    for i, name in enumerate(move_names, start=1):
        try:
            m = requests.get(f"{BASE}/move/{name}", timeout=10).json()
            print(f"Downloading move {i}/{limit}: {name}")

            meta = m.get("meta") or {}
            ailment = (meta.get("ailment") or {}).get("name", "none")
            category = (meta.get("category") or {}).get("name", "")
            damage_class = m["damage_class"]["name"]
            target_name = (m.get("target") or {}).get("name", "selected-pokemon")
            stat_chance = meta.get("stat_chance", 0)

            # Short effect text in English — used for charge/recharge detection
            effect_short = next(
                (e["short_effect"] for e in m.get("effect_entries", []) if e["language"]["name"] == "en"),
                ""
            ).lower()

            # Full effect description shown to the user
            effect_description = next(
                (e["effect"] for e in m.get("effect_entries", []) if e["language"]["name"] == "en"),
                ""
            )

            # Split stat_changes into three categories using target + damage_class + stat_chance
            user_stat_drops = {}    # e.g. Leaf Storm: {special-attack: -2}
            user_stat_boosts = {}   # e.g. Swords Dance: {attack: +2}
            enemy_stat_drops = {}   # e.g. Charm: {attack: -2}, Crunch: {special-defense: -1}

            for sc in m.get("stat_changes", []):
                stat_name = sc["stat"]["name"]
                change = sc.get("change", 0)

                if change > 0:
                    # Positive boosts targeting the user (setup moves)
                    if target_name == "user":
                        user_stat_boosts[stat_name] = change

                elif change < 0:
                    if damage_class == "status":
                        # Status moves: affects opponent → enemy drop; affects user → user drop
                        if target_name in ("selected-pokemon", "all-opponents", "all-other-pokemon"):
                            enemy_stat_drops[stat_name] = change
                        else:
                            user_stat_drops[stat_name] = change
                    else:
                        # Offensive move with stat drop:
                        # 0 < stat_chance < 100: probabilistic secondary effect on opponent (Crunch 20%)
                        # stat_chance == 100: guaranteed self-penalty on user (Close Combat, Superpower)
                        # stat_chance == 0: guaranteed self-penalty on offensive stat (Leaf Storm, Draco Meteor)
                        if 0 < stat_chance < 100:
                            enemy_stat_drops[stat_name] = change
                        else:
                            user_stat_drops[stat_name] = change

            dataset.append({
                "name": name,
                "type": m["type"]["name"],
                "damage_class": damage_class,
                "power": m["power"],
                "accuracy": m["accuracy"],
                # Turn mechanics and priority
                "priority": m.get("priority", 0),      # +1 Quick Attack, +2 Extreme Speed, -7 Trick Room
                "pp": m.get("pp"),                      # total PP
                "target": target_name,                  # selected-pokemon, user, all-opponents, ally...
                # Effects on the user
                "recoil": meta.get("recoil", 0),
                "drain": meta.get("drain", 0),
                "healing": meta.get("healing", 0),
                # Effects on the opponent
                "ailment": ailment,
                "ailment_chance": meta.get("ailment_chance", 0),
                "flinch_chance": meta.get("flinch_chance", 0),
                "stat_chance": stat_chance,
                # Hits and critical rate
                "crit_rate": meta.get("crit_rate", 0),  # 0=normal, 1=high crit chance
                "min_hits": meta.get("min_hits"),        # None or number for multi-hit
                "max_hits": meta.get("max_hits"),
                # Effect text (detects recharge, two-turn, etc.)
                "effect_short": effect_short,
                "description": effect_description,
                "meta_category": category,
                # Lock-in turns: how many turns the Pokemon is forced to use this move (e.g. Uproar = 3)
                "min_turns": meta.get("min_turns"),
                "max_turns": meta.get("max_turns"),
                # Stat changes split by affected party
                "user_stat_drops": user_stat_drops,     # {stat: change} self-penalties
                "user_stat_boosts": user_stat_boosts,   # {stat: change} self-boosts
                "enemy_stat_drops": enemy_stat_drops,   # {stat: change} opponent debuffs
            })
        except Exception:
            continue

    return dataset


def load_or_create_moves_dataset(limit=950):
    if os.path.exists(MOVES_PATH):
        with open(MOVES_PATH, "r") as f:
            return json.load(f)

    dataset = load_moves_dataset(limit)

    os.makedirs("data", exist_ok=True)
    with open(MOVES_PATH, "w") as f:
        json.dump(dataset, f)

    return dataset


# -----------------------------
# FULL POKEMON
# -----------------------------
def get_full_pokemon(name, is_legendary=False):
    if name in cache:
        return cache[name]

    data = requests.get(f"{BASE}/pokemon/{name}", timeout=10).json()

    types = [t["type"]["name"] for t in data["types"]]
    stats = {stat["stat"]["name"]: stat["base_stat"] for stat in data["stats"]}

    ability_name = data["abilities"][0]["ability"]["name"]
    sprite = data["sprites"]["front_default"]

    # Fetch ability description
    ability_desc = ""
    try:
        ab_data = requests.get(f"{BASE}/ability/{ability_name}", timeout=10).json()
        ability_desc = next(
            (e["effect"] for e in ab_data.get("effect_entries", []) if e["language"]["name"] == "en"),
            next(
                (e["flavor_text"] for e in ab_data.get("flavor_text_entries", [])
                 if e["language"]["name"] == "en"),
                ""
            )
        )
    except Exception:
        pass

    # Only move names — cross-referenced with moves dataset later
    moves = [m["move"]["name"] for m in data["moves"]]

    pokemon = Pokemon(
        name=name,
        types=types,
        stats=stats,
        ability=ability_name,
        ability_description=ability_desc,
        sprite=sprite,
        moves=moves,
        is_legendary=is_legendary,
    )

    cache[name] = pokemon
    return pokemon
