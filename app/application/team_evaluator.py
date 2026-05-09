from collections import Counter

from app.application.type_coverage import (
    team_defensive_weaknesses,
    team_offensive_coverage,
    type_synergy_score,
)

ALL_18 = 18


def evaluate_team(team) -> int:
    names = [p["name"] for p in team]
    if len(set(names)) < 6:
        return -100000

    score = 0

    # --- Offensive coverage ---
    # How many of the 18 types the team can hit super-effectively
    covered = team_offensive_coverage(team)
    score += len(covered) * 300
    if len(covered) >= 15:
        score += 2000
    elif len(covered) >= 12:
        score += 1000

    # --- Shared defensive weaknesses ---
    # Heavily penalize when multiple Pokemon share the same weakness
    weaknesses = team_defensive_weaknesses(team)
    for t, count in weaknesses.items():
        if count >= 4:
            score -= count * 800
        elif count >= 3:
            score -= count * 300
        elif count == 2:
            score -= count * 50

    # --- Type synergy ---
    # Bonus when a Pokemon resists its teammates' weaknesses
    score += type_synergy_score(team)

    # --- Type diversity ---
    # Penalize excessive concentration of the same type
    all_types = []
    for p in team:
        all_types.extend(p["types"])
    type_counts = Counter(all_types)
    for t, count in type_counts.items():
        if count >= 3:
            score -= (count - 2) * 500

    # --- Stat balance ---
    physical = sum(1 for p in team if p["stats"]["attack"] > 100)
    special = sum(1 for p in team if p["stats"]["special-attack"] > 100)
    fast = sum(1 for p in team if p["stats"]["speed"] > 100)
    bulky = sum(
        1
        for p in team
        if p["stats"]["hp"] * (p["stats"]["defense"] + p["stats"]["special-defense"]) / 2
        > 14000
    )

    if physical >= 2:
        score += 400
    if special >= 2:
        score += 400
    if physical >= 1 and special >= 1:
        score += 500  # mixed offense
    if fast >= 2:
        score += 300
    if bulky >= 1:
        score += 300

    return score
