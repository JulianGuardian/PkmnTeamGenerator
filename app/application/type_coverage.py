import json
import os
from collections import Counter

_path = os.path.join(os.path.dirname(__file__), "../../data/type_chart.json")
TYPE_CHART = json.load(open(_path))
ALL_TYPES = list(TYPE_CHART.keys())  # 18 types


def _types(p):
    return p["types"] if isinstance(p, dict) else p.types


def type_effectiveness(attacking_type: str, defending_types: list) -> float:
    """Damage multiplier of attacking_type against a Pokémon with defending_types."""
    data = TYPE_CHART.get(attacking_type, {})
    mult = 1.0
    for dt in defending_types:
        if dt in data.get("immunes", []):
            return 0.0
        if dt in data.get("strengths", []):
            mult *= 2.0
        elif dt in data.get("weaknesses", []):
            mult *= 0.5
    return mult


def offensive_coverage(types: list) -> set:
    """Set of types hit super-effectively by STAB moves of given types."""
    covered = set()
    for t in types:
        covered.update(TYPE_CHART.get(t, {}).get("strengths", []))
    return covered


def move_coverage(move_type: str) -> set:
    """Set of types hit super-effectively by a move of move_type."""
    return set(TYPE_CHART.get(move_type, {}).get("strengths", []))


def pokemon_weaknesses(types: list) -> set:
    """Attacking types that deal 2x or 4x damage to a Pokémon with these types."""
    return {at for at in ALL_TYPES if type_effectiveness(at, types) >= 2.0}


def pokemon_resistances(types: list) -> set:
    """Attacking types that deal 0.5x or 0.25x damage."""
    return {at for at in ALL_TYPES if 0 < type_effectiveness(at, types) <= 0.5}


def pokemon_immunities(types: list) -> set:
    """Attacking types that deal 0 damage."""
    return {at for at in ALL_TYPES if type_effectiveness(at, types) == 0.0}


def team_offensive_coverage(team: list) -> set:
    """All types any team member's STAB moves can hit super-effectively."""
    covered = set()
    for p in team:
        covered.update(offensive_coverage(_types(p)))
    return covered


def team_defensive_weaknesses(team: list) -> Counter:
    """Counter of how many team members are weak to each attacking type."""
    counter = Counter()
    for p in team:
        for w in pokemon_weaknesses(_types(p)):
            counter[w] += 1
    return counter


def type_synergy_score(team: list) -> int:
    """Rewards when a Pokémon resists the weaknesses of its teammates."""
    score = 0
    for i, p in enumerate(team):
        p_weak = pokemon_weaknesses(_types(p))
        for j, q in enumerate(team):
            if i == j:
                continue
            q_safe = pokemon_resistances(_types(q)) | pokemon_immunities(_types(q))
            score += len(p_weak & q_safe) * 50
    return score
