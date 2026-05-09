from app.application.type_coverage import move_coverage, offensive_coverage

# =========================
# SINGLES-ONLY TARGET FILTER
# =========================
# "ally"           — only affects the partner in doubles, useless in singles
# "fainting-pokemon" — revival mechanic, useless in normal battle
# "all-other-pokemon" (Surf, Earthquake, Discharge) hits everyone except the user:
#   in doubles it also hits the partner, but in singles it just hits the opponent — useful
DOUBLES_ONLY_TARGETS = {"ally", "fainting-pokemon"}

BANNED_MOVES = {
    # Mandatory recharge turn after attacking (also caught by is_charge_move, explicit fallback)
    "giga-impact", "hyper-beam", "rock-wrecker",
    "roar-of-time", "blast-burn", "hydro-cannon", "frenzy-plant",
    "eternabeam", "meteor-assault",
    # Self-KO moves
    "explosion", "self-destruct", "final-gambit", "mind-blown",
    # Team-sacrifice moves (user permanently exits the battle)
    "healing-wish", "lunar-dance", "memento",
    # Massive self-damage
    "steel-beam",
    # One-hit KO: broken mechanic, base accuracy 30
    "guillotine", "horn-drill", "fissure", "sheer-cold",
    # Two-turn charge moves (explicit fallback alongside effect_short filter)
    "sky-attack", "solar-beam", "solar-blade", "skull-bash",
    "fly", "dig", "dive", "bounce",
    "shadow-force", "phantom-force", "sky-drop",
    "freeze-shock", "ice-burn", "geomancy", "prismatic-laser",
}

LOW_QUALITY_MOVES = {
    # ── HM legacy (low power or no competitive use) ───────────────────────────
    "cut", "strength", "rock-smash",

    # ── Completely useless / casual-only moves ────────────────────────────────
    "splash", "celebrate", "hold-hands", "happy-hour",

    # ── Friendship / unrepeatable external condition dependent ────────────────
    "frustration", "return", "veevee-volley", "natural-gift",
    "present",          # random damage OR heals the opponent — terrible

    # ── Self evasion (banned in official competitive) ─────────────────────────
    "minimize", "double-team",

    # ── Lowers opponent's accuracy / evasion (equally uncompetitive) ─────────
    "sand-attack", "smokescreen", "flash", "mud-slap",
    "sweet-scent", "kinesis",

    # ── Lowers only -1 in one stat with no damage (not worth a moveslot) ──────
    "growl", "leer", "tail-whip", "string-shot",
    "play-nice", "confide",

    # ── Raises only +1 in one stat with no further effect (not worth a slot) ──
    "meditate", "harden", "sharpen", "howl",
    "defense-curl", "withdraw",

    # ── Ridiculously fixed damage (20 or 40 always, useless past level 20) ────
    "sonic-boom", "dragon-rage",

    # ── Variable / HP- or PP-dependent damage — too unreliable ───────────────
    "psywave",          # level × random 0.5–1.5
    "magnitude",        # varies from 10 to 150, unpredictable
    "flail", "reversal",        # only useful near fainting
    "wring-out", "crush-grip",  # only good when opponent is at full HP
    "trump-card",               # power rises with fewer PP remaining — very situational

    # ── Trapping moves (no value in standard singles) ─────────────────────────
    "block", "mean-look", "spider-web",

    # ── Doubles-only (affect partner or whole field) ──────────────────────────
    "after-you", "ally-switch", "coaching", "crafty-shield",
    "decorate", "follow-me", "flower-shield", "gear-up",
    "helping-hand", "instruct", "mat-block", "quash",
    "rage-powder", "rototiller", "spotlight", "wide-guard",

    # ── Complete randomness (no control over the effect) ─────────────────────
    "metronome", "assist", "nature-power",

    # ── Copy / imitate opponent moves (too situational) ───────────────────────
    "mimic", "copycat", "me-first",
    "sketch",           # Smeargle-specific, irrelevant in team builder
    "transform",        # Ditto-specific

    # ── Type manipulation (provides no direct damage or control) ─────────────
    "camouflage", "conversion", "conversion-2", "reflect-type",
    "soak", "magic-powder", "trick-or-treat", "forests-curse",

    # ── Ability manipulation (too situational in singles) ────────────────────
    "role-play", "skill-swap", "simple-beam", "entrainment",
    "worry-seed", "gastro-acid",

    # ── Revenge moves that require taking damage first ────────────────────────
    "counter", "mirror-coat", "metal-burst",
    "bide",             # stores damage and returns ×2 — too passive

    # ── Wasted turn with no direct effect ────────────────────────────────────
    "rage",             # de-facto lock-in with minimal attack boost
    "spite",            # reduces opponent's last move PP — very niche
    "recycle",          # recovers held item — requires external setup
    "imprison",         # blocks shared moves — too niche
    "lock-on", "mind-reader",   # ensures next move hits — evasion barely matters
    "laser-focus",              # guaranteed crit next turn — one turn wasted
    "acupressure",              # +2 to a random stat — unreliable
    "ion-deluge",               # converts normal moves to electric — extreme niche
    "topsy-turvy",              # reverses stat changes — too situational
    "venom-drench",             # only works on poisoned targets
    "teatime",                  # everyone eats their berry — no real value
    "magic-room",               # suppresses items — too niche
    "wonder-room",              # swaps Def/SpDef for all — too niche
    "psych-up",                 # copies opponent's stat changes — better to set up yourself
    "haze",                     # resets all stat changes — taunt is usually better

    # ── Situational mechanics that don't contribute in singles ───────────────
    "last-resort",      # only works after using every other move
    "quick-guard",      # blocks priority moves for the team — doubles move
    "feint",            # only hits through Protect — situational
    "detect",           # worse Protect (fewer PP)
    "attract",          # requires opposite gender
    "foresight", "odor-sleuth",  # removes ghost/dark immunity — very niche

    # ── Requires active terrain or external conditions ────────────────────────
    "steel-roller",     # fails without active terrain

    # ── Requires consuming a berry / specific held item ───────────────────────
    "stuff-cheeks",

    # ── Lock-in + confusion moves not caught by is_lockin_move ───────────────
    # outrage, thrash, petal-dance → caught by "confused after" in effect_short
}

# Known setup move names by category (fallback when user_stat_boosts is empty in dataset)
SETUP_MOVES_NAMES = {
    "offensive":  {"swords-dance", "dragon-dance", "nasty-plot", "tail-glow",
                   "quiver-dance", "shift-gear", "victory-dance"},
    "defensive":  {"iron-defense", "amnesia", "barrier", "acid-armor",
                   "cosmic-power", "stockpile", "bulk-up", "calm-mind"},
    "mixed":      {"bulk-up", "calm-mind", "coil", "quiver-dance",
                   "dragon-dance", "shift-gear"},
}

# Pivot moves (deal damage + switch out)
PIVOT_MOVES = {"u-turn", "volt-switch", "flip-turn", "parting-shot"}

# Stall / field control moves
STALL_MOVES = {
    "toxic", "protect", "substitute", "will-o-wisp",
    "leech-seed", "spikes", "stealth-rock", "toxic-spikes",
}

# Recovery move names (fallback for moves without healing > 0 in the API)
RECOVERY_MOVES_NAMES = {
    "recover", "roost", "slack-off", "soft-boiled", "rest",
    "moonlight", "morning-sun", "synthesis", "shore-up",
    "jungle-healing", "life-dew",
}


# =========================
# DATA HELPERS
# =========================

def is_recoil_move(move: dict) -> bool:
    return move.get("recoil", 0) <= -33


def is_faint_move(move: dict) -> bool:
    return move.get("recoil", 0) <= -100


def is_charge_move(move: dict) -> bool:
    """Detects moves that waste a turn — either charging before or recharging after.
    Uses effect_short because min_turns is null for these cases in the current API.
    - 'recharge': useless turn AFTER the attack (Giga Impact, Rock Wrecker)
    - 'next turn' / 'second turn': charges one turn and attacks the next (Fly, Dig, Solar Beam)
    """
    effect = (move.get("effect_short") or "").lower()
    return "recharge" in effect or "next turn" in effect or "second turn" in effect


def is_lockin_move(move: dict) -> bool:
    """Detects moves that force the Pokemon to keep using them for several turns.
    Uses min_turns when the API provides it (e.g. Uproar = 3 turns).
    For Outrage/Thrash/Petal Dance the API reports min_turns=null, detected via effect_short.
    """
    min_turns = move.get("min_turns")
    if min_turns is not None and min_turns >= 2:
        return True
    effect = (move.get("effect_short") or "").lower()
    # "confused after" covers Outrage, Thrash, Petal Dance ("user becomes confused after")
    return "confused after" in effect


def self_debuffs_main_attack(move: dict) -> bool:
    """Drops the user's own offensive stat by -2 or more (Leaf Storm, Draco Meteor, Overheat…)."""
    drops = move.get("user_stat_drops") or {}
    for stat, change in drops.items():
        if stat in {"attack", "special-attack"} and change <= -2:
            return True
    return False


def is_recovery_move(move: dict) -> bool:
    return move["name"] in RECOVERY_MOVES_NAMES or (move.get("healing") or 0) > 0


def is_rest_move(move: dict) -> bool:
    return move["name"] == "rest"


def is_priority_move(move: dict) -> bool:
    return (move.get("priority") or 0) >= 1


def _setup_total(move: dict) -> int:
    """Total boost points across all user stats."""
    return sum((move.get("user_stat_boosts") or {}).values())


def is_setup_move(move: dict) -> bool:
    """A setup move is any move that meaningfully improves the user's own stats:
    - One stat rises >= 2, OR
    - Multiple stats rise summing >= 2 total (e.g. Dragon Dance: +1 atk +1 speed = 2)
    Includes both offensive and defensive setup.
    """
    all_names = SETUP_MOVES_NAMES["offensive"] | SETUP_MOVES_NAMES["defensive"]
    if move["name"] in all_names:
        return True
    return _setup_total(move) >= 2


def is_offensive_setup(move: dict) -> bool:
    """Setup that raises offensive stats (attack, special-attack, speed)."""
    offensive_stats = {"attack", "special-attack", "speed"}
    if move["name"] in SETUP_MOVES_NAMES["offensive"]:
        return True
    boosts = move.get("user_stat_boosts") or {}
    offensive_boost = sum(v for s, v in boosts.items() if s in offensive_stats)
    return offensive_boost >= 2


def is_physical_setup(move: dict) -> bool:
    """Setup that raises physical attack or speed — for physical sweepers."""
    physical_stats = {"attack", "speed"}
    if move["name"] in {"swords-dance", "dragon-dance", "shift-gear", "victory-dance"}:
        return True
    boosts = move.get("user_stat_boosts") or {}
    phys_boost = sum(v for s, v in boosts.items() if s in physical_stats)
    return phys_boost >= 2


def is_special_setup(move: dict) -> bool:
    """Setup that raises special attack — for special sweepers."""
    special_stats = {"special-attack", "speed"}
    if move["name"] in {"nasty-plot", "tail-glow", "quiver-dance", "calm-mind"}:
        return True
    boosts = move.get("user_stat_boosts") or {}
    spec_boost = sum(v for s, v in boosts.items() if s in special_stats)
    return spec_boost >= 2


def is_defensive_setup(move: dict) -> bool:
    """Setup that raises defensive stats (defense, special-defense)."""
    defensive_stats = {"defense", "special-defense"}
    if move["name"] in SETUP_MOVES_NAMES["defensive"]:
        return True
    boosts = move.get("user_stat_boosts") or {}
    defensive_boost = sum(v for s, v in boosts.items() if s in defensive_stats)
    return defensive_boost >= 2


def is_enemy_debuff_move(move: dict) -> bool:
    """Move that lowers the opponent's stats (Charm, Screech, Crunch secondary effect…)."""
    return bool(move.get("enemy_stat_drops"))


def is_drain_move(move: dict) -> bool:
    return (move.get("drain") or 0) > 0


def has_secondary_effect(move: dict) -> bool:
    return (
        (move.get("ailment_chance") or 0) > 0
        or (move.get("flinch_chance") or 0) > 0
        or (move.get("stat_chance") or 0) > 0
    )


def expected_power(move: dict) -> float:
    """Expected real power accounting for multi-hit moves."""
    base = move.get("power") or 0
    min_h = move.get("min_hits")
    max_h = move.get("max_hits")
    if min_h and max_h:
        return base * (min_h + max_h) / 2
    return float(base)


# =========================
# PREFERRED DAMAGE CLASS
# =========================

def _preferred_damage_class(pokemon):
    """Forces specialization if the difference between attack and sp_attack exceeds 20 points."""
    diff = pokemon.attack - pokemon.sp_attack
    if diff > 20:
        return "physical"
    if diff < -20:
        return "special"
    return None  # mixed


# =========================
# TEAM HELPERS
# =========================

def get_avg_speed(team) -> float:
    return sum(p.speed for p in team) / len(team)


def is_stab(move: dict, pokemon) -> bool:
    return move["type"] in pokemon.types


def has_duplicate_type(move: dict, moveset: list) -> bool:
    if move["damage_class"] == "status":
        return False
    for m in moveset:
        if m["damage_class"] != "status" and m["type"] == move["type"]:
            return True
    return False


def _team_covered_types(team, exclude_pokemon) -> set:
    covered = set()
    for p in team:
        if p.name != exclude_pokemon.name:
            covered.update(offensive_coverage(p.types))
    return covered


# =========================
# MAIN FILTER
# =========================

def filter_valid_moves(pokemon, team, moves_dataset: list) -> list:
    preferred = _preferred_damage_class(pokemon)
    avg_speed = get_avg_speed(team)
    filtered = []

    for m in moves_dataset:
        if m["name"] not in pokemon.moves:
            continue

        name = m["name"]
        target = m.get("target", "selected-pokemon")

        if name in BANNED_MOVES or name in LOW_QUALITY_MOVES:
            continue

        if target in DOUBLES_ONLY_TARGETS:
            continue

        if is_faint_move(m) or is_recoil_move(m):
            continue

        if is_charge_move(m):
            continue

        if is_lockin_move(m):
            continue

        if self_debuffs_main_attack(m):
            continue

        # Rest only makes sense on bulky Pokemon
        if is_rest_move(m):
            bulk = pokemon.hp * (pokemon.defense + pokemon.sp_defense) / 2
            if bulk < 12000:
                continue

        # Minimum accuracy threshold
        if (m.get("accuracy") or 101) < 70:
            continue

        # Trick Room only for slow teams
        if name == "trick-room" and avg_speed > 90:
            continue

        # Respect the Pokemon's dominant damage class for offensive moves
        if m["damage_class"] != "status" and m.get("power"):
            if preferred == "physical" and m["damage_class"] == "special":
                continue
            if preferred == "special" and m["damage_class"] == "physical":
                continue
            # Discard physical moves if physical attack is negligible (e.g. Shuckle)
            if m["damage_class"] == "physical" and pokemon.attack < 40:
                continue
            # Discard special moves if special attack is negligible
            if m["damage_class"] == "special" and pokemon.sp_attack < 40:
                continue

        filtered.append(m)

    return filtered


# =========================
# MOVE POOL CLASSIFICATION
# =========================

def classify_moves(valid_moves: list):
    physical = [m for m in valid_moves if m["damage_class"] == "physical" and m.get("power")]
    special  = [m for m in valid_moves if m["damage_class"] == "special"   and m.get("power")]
    status   = [m for m in valid_moves if m["damage_class"] == "status"]
    return physical, special, status


def get_offensive_pools(pokemon, valid_moves: list):
    physical, special, status = classify_moves(valid_moves)
    preferred = _preferred_damage_class(pokemon)
    if preferred == "physical":
        pool = physical
    elif preferred == "special":
        pool = special
    else:
        pool = physical + special
    stab     = [m for m in pool if is_stab(m, pokemon)]
    non_stab = [m for m in pool if not is_stab(m, pokemon)]
    return stab, non_stab, status


# =========================
# COMPETITIVE SCORING
# =========================

def score_move(move: dict, pokemon, uncovered_types: set = None, role: str = None) -> float:
    score = 0.0
    name  = move["name"]
    power = expected_power(move)
    acc   = move.get("accuracy") or 100

    score += power
    score += (acc - 70) * 0.5
    # Heavily penalize low-power moves so they don't compete with viable options
    if power > 0 and power < 50:
        score -= (50 - power) * 2

    # STAB bonus
    if move["type"] in pokemon.types:
        score += 30

    # Coverage for types the rest of the team doesn't cover
    if uncovered_types:
        new_covered = move_coverage(move["type"]) & uncovered_types
        score += len(new_covered) * 80

    # Priority — very valuable for revenge killers
    priority = move.get("priority") or 0
    if priority >= 2:
        score += 50
    elif priority == 1:
        score += 25

    # Increased critical hit rate
    crit = move.get("crit_rate") or 0
    if crit > 0:
        score += 20 * crit

    # Secondary effects
    if has_secondary_effect(move):
        score += (move.get("ailment_chance") or 0) * 0.3
        score += (move.get("flinch_chance")  or 0) * 0.2
        score += (move.get("stat_chance")    or 0) * 0.2

    # Drain (damage + recovery)
    if is_drain_move(move):
        score += 20

    # Opponent debuff (valuable for annoyers and balanced)
    if is_enemy_debuff_move(move):
        drops = move.get("enemy_stat_drops") or {}
        score += sum(abs(v) for v in drops.values()) * 15

    # Setup: bonus proportional to total boost points
    total_boost = _setup_total(move)
    if total_boost >= 2 or is_setup_move(move):
        score += 20 + total_boost * 8

    # Recovery
    if is_recovery_move(move):
        score += 35

    # Pivot
    if name in PIVOT_MOVES:
        score += 40

    # Classic competitive utility bonus
    UTILITY_BONUS = {
        "stealth-rock": 50, "defog": 50, "rapid-spin": 50, "taunt": 50,
        "knock-off": 40, "encore": 35, "spikes": 35,
    }
    score += UTILITY_BONUS.get(name, 0)

    # Meta bonus (moves with proven competitive value)
    META_BONUS = {
        "earthquake": 40, "close-combat": 40, "stone-edge": 35,
        "moonblast": 35, "thunderbolt": 35, "ice-beam": 35,
        "shadow-ball": 30, "flamethrower": 30, "surf": 30,
        "psychic": 25, "energy-ball": 25, "dragon-claw": 25,
        "iron-head": 25, "play-rough": 30, "extreme-speed": 35,
    }
    score += META_BONUS.get(name, 0)

    return score


# =========================
# MOVE SELECTION
# =========================

def pick_best_moves(pool: list, pokemon, k: int = 1,
                    existing: list = None, uncovered_types: set = None,
                    role: str = None) -> list:
    if existing is None:
        existing = []
    ranked = sorted(pool, key=lambda m: score_move(m, pokemon, uncovered_types, role), reverse=True)
    selected = []
    for move in ranked:
        if len(selected) >= k:
            break
        if has_duplicate_type(move, existing + selected):
            continue
        selected.append(move)
    return selected


def pick_role_moves(role: str, pokemon, stab, non_stab, status,
                    valid_moves: list, uncovered_types: set) -> list:
    moveset = []

    if role in ("physical_sweeper", "special_sweeper"):
        moveset += pick_best_moves(stab, pokemon, 2, moveset, role=role)
        moveset += pick_best_moves(non_stab, pokemon, 1, moveset, uncovered_types, role)
        # Role-specific setup
        if role == "physical_sweeper":
            setup_pool = [m for m in status if is_physical_setup(m)]
        else:
            setup_pool = [m for m in status if is_special_setup(m)]
        if setup_pool:
            moveset += pick_best_moves(setup_pool, pokemon, 1, moveset)
        else:
            # No appropriate setup available: add extra offensive coverage instead
            moveset += pick_best_moves(non_stab, pokemon, 1, moveset, uncovered_types, role)

    elif role == "tank":
        moveset += pick_best_moves(stab, pokemon, 1, moveset, role=role)
        # Drain for sustain
        drain = [m for m in (stab + non_stab) if is_drain_move(m)]
        moveset += pick_best_moves(drain, pokemon, 1, moveset)
        # Defensive setup
        def_setup = [m for m in status if is_defensive_setup(m)]
        moveset += pick_best_moves(def_setup, pokemon, 1, moveset)
        recovery = [m for m in status if is_recovery_move(m)]
        moveset += pick_best_moves(recovery, pokemon, 1, moveset)

    elif role == "annoyer":
        # Priority: opponent debuffs > status conditions > defensive setup > recovery
        debuff = [m for m in status if is_enemy_debuff_move(m)]
        moveset += pick_best_moves(debuff, pokemon, 1, moveset)
        ailment = [m for m in status if (m.get("ailment") or "none") not in {"none", ""}]
        moveset += pick_best_moves(ailment, pokemon, 1, moveset)
        def_setup = [m for m in status if is_defensive_setup(m)]
        moveset += pick_best_moves(def_setup, pokemon, 1, moveset)
        recovery = [m for m in status if is_recovery_move(m)]
        moveset += pick_best_moves(recovery, pokemon, 1, moveset)

    elif role == "revenge_killer":
        # First slot: priority move if available
        prio_moves = [m for m in (stab + non_stab) if is_priority_move(m)]
        moveset += pick_best_moves(prio_moves, pokemon, 1, moveset, role=role)
        moveset += pick_best_moves(stab, pokemon, 2, moveset, role=role)
        pivot = [m for m in valid_moves if m["name"] in PIVOT_MOVES]
        moveset += pick_best_moves(pivot, pokemon, 1, moveset)
        moveset += pick_best_moves(non_stab, pokemon, 1, moveset, uncovered_types, role)

    else:  # balanced
        moveset += pick_best_moves(stab, pokemon, 1, moveset, role=role)
        moveset += pick_best_moves(non_stab, pokemon, 1, moveset, uncovered_types, role)
        # Setup based on the Pokemon's dominant offensive stat
        if pokemon.sp_attack >= pokemon.attack:
            setup_pool = [m for m in status if is_special_setup(m)]
        else:
            setup_pool = [m for m in status if is_physical_setup(m)]
        if not setup_pool:
            setup_pool = [m for m in status if is_setup_move(m)]
        moveset += pick_best_moves(setup_pool, pokemon, 1, moveset)
        utility = [m for m in status if m["name"] in {"stealth-rock", "defog", "taunt"}]
        moveset += pick_best_moves(utility, pokemon, 1, moveset)

    return moveset


def complete_moveset(moveset: list, valid_moves: list, pokemon,
                     uncovered_types: set = None) -> list:
    """Fills up to 4 slots respecting the dominant damage class and prioritizing coverage."""
    remaining = [m for m in valid_moves if m not in moveset]
    preferred = _preferred_damage_class(pokemon)

    def is_allowed(m):
        if m["damage_class"] == "status":
            return True
        if preferred and m["damage_class"] != preferred:
            return False
        return True

    remaining = [m for m in remaining if is_allowed(m)]

    coverage = [m for m in remaining if move_coverage(m["type"]) & (uncovered_types or set())]
    other    = [m for m in remaining if m not in coverage]

    ordered = (
        sorted(coverage, key=lambda m: score_move(m, pokemon, uncovered_types), reverse=True)
        + sorted(other,  key=lambda m: score_move(m, pokemon),                  reverse=True)
    )

    for m in ordered:
        if len(moveset) >= 4:
            break
        if has_duplicate_type(m, moveset):
            continue
        moveset.append(m)

    return moveset[:4]


# =========================
# MAIN GENERATOR
# =========================

def generate_moveset(pokemon, role: str, moves_dataset: list, team) -> list:
    valid_moves = filter_valid_moves(pokemon, team, moves_dataset)
    if not valid_moves:
        return []

    from app.application.type_coverage import ALL_TYPES
    team_covered    = _team_covered_types(team, pokemon)
    uncovered_types = set(ALL_TYPES) - team_covered

    stab, non_stab, status = get_offensive_pools(pokemon, valid_moves)

    moveset = pick_role_moves(role, pokemon, stab, non_stab, status, valid_moves, uncovered_types)
    moveset = complete_moveset(moveset, valid_moves, pokemon, uncovered_types)

    # Guarantee at least 1 damaging move
    has_damaging = any(m.get("power") and m["damage_class"] != "status" for m in moveset)
    if not has_damaging:
        offensive_pool_sorted = sorted(
            stab + non_stab,
            key=lambda m: score_move(m, pokemon, uncovered_types, role),
            reverse=True,
        )
        if offensive_pool_sorted:
            moveset = moveset[:3] + [offensive_pool_sorted[0]]

    return moveset[:4]
