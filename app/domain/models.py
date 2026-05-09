class Move:
    def __init__(self, name, type):
        self.name = name
        self.type = type


class Pokemon:
    def __init__(self, name, types, stats, ability, sprite, moves,
                 is_legendary=False, ability_description=""):
        self.name = name
        self.types = types
        self.ability = ability
        self.ability_description = ability_description
        self.sprite = sprite
        self.moves = moves
        self.is_legendary = is_legendary

        self.hp = stats["hp"]
        self.attack = stats["attack"]
        self.defense = stats["defense"]
        self.sp_attack = stats["special-attack"]
        self.sp_defense = stats["special-defense"]
        self.speed = stats["speed"]
