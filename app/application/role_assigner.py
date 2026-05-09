def assign_role(stats):
    atk = stats["attack"]
    spa = stats["special-attack"]
    speed = stats["speed"]
    hp = stats["hp"]
    defense = stats["defense"]
    spdef = stats["special-defense"]

    bulk = hp * (defense + spdef) / 2

    # High classic bulk OR extreme individual defense with low speed (e.g. Probopass)
    is_wall = bulk > 18000 or (defense > 130 and spdef > 100 and speed < 60)
    if is_wall and speed < 80:
        return "annoyer"

    if speed > 120:
        return "revenge_killer"

    if atk > 120:
        return "physical_sweeper"

    if spa > 120:
        return "special_sweeper"

    if bulk > 15000:
        return "tank"

    return "balanced"
