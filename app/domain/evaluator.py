from collections import Counter

TYPE_WEAKNESS = {
    "flying": ["electric", "rock"],
    "water": ["electric", "grass"],
    "dragon": ["ice", "fairy"],
    "dark": ["fairy", "fighting"],
}


def evaluate_team(team):
    score = 0

    physical = 0
    special = 0
    tanks = 0
    fast = 0

    all_types = []
    weaknesses = []

    names = [p["name"] for p in team]

    if len(set(names)) < 6:
        return -100

    for p in team:
        stats = p["stats"]

        atk = stats["attack"]
        spa = stats["special-attack"]

        if atk > 110:
            physical += 1
            score += 10

        if spa > 110:
            special += 1
            score += 10

        bulk = stats["hp"] * (stats["defense"] + stats["special-defense"]) / 2
        if bulk > 14000:
            tanks += 1
            score += 15

        if stats["speed"] > 100:
            fast += 1
            score += 10

        for t in p["types"]:
            all_types.append(t)
            if t in TYPE_WEAKNESS:
                weaknesses.extend(TYPE_WEAKNESS[t])

    if physical >= 2:
        score += 25
    if special >= 2:
        score += 25
    if tanks >= 2:
        score += 30
    if fast >= 2:
        score += 20

    unique_types = len(set(all_types))
    score += unique_types * 3

    weak_count = Counter(weaknesses)
    for w, count in weak_count.items():
        if count >= 3:
            score -= count * 8

    return score


_ROLE_BASE = {
    "physical_sweeper": "Physical attack specialist that aims to overwhelm opponents with raw power.",
    "special_sweeper":  "Special attack specialist that dominates with high-power magical moves.",
    "revenge_killer":   "Comes in to eliminate weakened opponents thanks to its exceptional speed or priority moves.",
    "annoyer":          "Wears down the opponent through status conditions, defensive setup, and recovery.",
    "tank":             "Absorbs hits due to its high bulk and deals sustained damage in return.",
    "balanced":         "Versatile profile that combines offense, coverage, and a degree of durability.",
}


def explain_pokemon(p, role: str) -> str:
    traits = []

    if role != "special_sweeper" and p.attack > 110:
        traits.append("very high physical attack")
    if role != "physical_sweeper" and p.sp_attack > 110:
        traits.append("very high special attack")
    if p.defense > 110:
        traits.append("outstanding physical defense")
    if p.sp_defense > 110:
        traits.append("outstanding special defense")
    if p.speed > 110:
        traits.append("exceptional speed")
    elif p.speed > 90:
        traits.append("good speed")

    bulk = p.hp * (p.defense + p.sp_defense) / 2
    if bulk > 18000:
        traits.append("extremely high bulk")
    elif bulk > 12000:
        traits.append("solid bulk")

    base = _ROLE_BASE.get(role, "Balanced role with no extreme stats.")
    if traits:
        return f"{base} Notable stats: {', '.join(traits)}."
    return base
