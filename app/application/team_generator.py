import random
from collections import Counter

from app.application.role_assigner import assign_role
from app.application.team_evaluator import evaluate_team
from app.application.type_coverage import team_offensive_coverage

# Explicit list of legendaries/mythicals as fallback when dataset field is unreliable
KNOWN_LEGENDARIES = {
    "articuno", "zapdos", "moltres", "mewtwo", "mew",
    "raikou", "entei", "suicune", "lugia", "ho-oh", "celebi",
    "regirock", "regice", "registeel", "latias", "latios",
    "kyogre", "groudon", "rayquaza", "jirachi", "deoxys",
    "uxie", "mesprit", "azelf", "dialga", "palkia", "heatran",
    "regigigas", "giratina", "cresselia", "phione", "manaphy",
    "darkrai", "shaymin", "arceus", "victini", "cobalion",
    "terrakion", "virizion", "tornadus", "thundurus", "reshiram",
    "zekrom", "landorus", "kyurem", "keldeo", "meloetta", "genesect",
    "xerneas", "yveltal", "zygarde", "diancie", "hoopa", "volcanion",
    "type-null", "silvally", "tapu-koko", "tapu-lele", "tapu-bulu",
    "tapu-fini", "cosmog", "cosmoem", "solgaleo", "lunala", "nihilego",
    "buzzwole", "pheromosa", "xurkitree", "celesteela", "kartana",
    "guzzlord", "necrozma", "magearna", "marshadow", "poipole",
    "naganadel", "stakataka", "blacephalon", "zeraora", "melmetal",
    "zacian", "zamazenta", "eternatus", "kubfu", "urshifu", "zarude",
    "regieleki", "regidrago", "glastrier", "spectrier", "calyrex",
    "enamorus", "wo-chien", "chien-pao", "ting-lu", "chi-yu",
    "koraidon", "miraidon",
}

# Minimum BST to ensure competitively viable Pokemon
# 400 filters pre-evolutions, but Pokemon like Raticate (413) are still too weak
# 450 excludes most low-tier Pokemon without losing role coverage
MIN_BST = 450


def _is_legendary(p):
    return p.get("is_legendary", False) or p["name"] in KNOWN_LEGENDARIES


class TeamGenerator:
    def __init__(self, dataset):
        self.dataset = [
            p for p in dataset
            if sum(p["stats"].values()) >= MIN_BST
        ]

    def random_team(self):
        legends = [p for p in self.dataset if _is_legendary(p)]
        non_legends = [p for p in self.dataset if not _is_legendary(p)]

        team = []
        if legends:
            team.append(random.choice(legends))

        remaining = 6 - len(team)
        team += random.sample(non_legends, remaining)

        random.shuffle(team)
        return team

    def fitness(self, team):
        score = 0

        for p in team:
            stats = p["stats"]
            score += stats["attack"] + stats["special-attack"] + stats["speed"]

        score += evaluate_team(team)
        role_counts = self.count_roles(team)
        score += self.role_diversity_bonus(role_counts)

        return score

    def count_roles(self, team):
        counts = Counter()
        for p in team:
            role = assign_role(p["stats"])
            counts[role] += 1
        return counts

    def count_legendaries(self, team):
        return sum(1 for p in team if _is_legendary(p))

    def role_diversity_bonus(self, counts):
        bonus = 0
        required_roles = [
            "annoyer",
            "revenge_killer",
            "physical_sweeper",
            "special_sweeper",
        ]
        for role in required_roles:
            if counts[role] > 0:
                bonus += 1000
            else:
                bonus -= 10000

        if counts["tank"] >= 2 or (counts["tank"] >= 1 and counts["balanced"] >= 1):
            bonus += 1000
        else:
            bonus -= 10000

        return bonus

    def meets_role_requirements(self, team):
        counts = self.count_roles(team)

        if counts["annoyer"] < 1:
            return False
        if counts["revenge_killer"] < 1:
            return False
        if counts["physical_sweeper"] < 1:
            return False
        if counts["special_sweeper"] < 1:
            return False
        if not (
            counts["tank"] >= 2 or (counts["tank"] >= 1 and counts["balanced"] >= 1)
        ):
            return False

        # No more than 2 Pokemon with the same primary type
        primary_types = Counter(p["types"][0] for p in team)
        if any(count >= 3 for count in primary_types.values()):
            return False

        # Team must cover at least 10 of the 18 types offensively
        if len(team_offensive_coverage(team)) < 10:
            return False

        return True

    def evolve(self, generations=20, population_size=20):
        population = [self.random_team() for _ in range(population_size)]

        for _ in range(generations):
            population = sorted(population, key=self.fitness, reverse=True)
            next_gen = population[:5]

            while len(next_gen) < population_size:
                parent = random.choice(population[:10])
                child = parent[:]

                # Mutation without duplicating a Pokemon
                idx = random.randint(0, 5)
                existing_names = {p["name"] for i, p in enumerate(child) if i != idx}
                existing_legendaries = self.count_legendaries(
                    [p for i, p in enumerate(child) if i != idx]
                )

                if existing_legendaries >= 1:
                    candidates = [
                        p
                        for p in self.dataset
                        if p["name"] not in existing_names and not _is_legendary(p)
                    ]
                else:
                    candidates = [
                        p for p in self.dataset if p["name"] not in existing_names
                    ]

                if candidates:
                    child[idx] = random.choice(candidates)

                next_gen.append(child)

            population = next_gen

        # Ensure the returned team has no duplicates
        best = max(population, key=self.fitness)
        seen = set()
        unique_team = []
        for p in best:
            if p["name"] not in seen:
                seen.add(p["name"])
                unique_team.append(p)
        if len(unique_team) < 6:
            remaining = [p for p in self.dataset if p["name"] not in seen]
            unique_team += random.sample(remaining, 6 - len(unique_team))

        # Cap at 1 legendary — if more than one, keep only the first and fill with non-legendaries
        if self.count_legendaries(unique_team) > 1:
            legends_in_team = [p for p in unique_team if _is_legendary(p)]
            non_legends_in_team = [p for p in unique_team if not _is_legendary(p)]
            unique_team = non_legends_in_team + [legends_in_team[0]]
            if len(unique_team) < 6:
                names_used = {p["name"] for p in unique_team}
                remaining = [
                    p for p in self.dataset
                    if p["name"] not in names_used and not _is_legendary(p)
                ]
                unique_team += random.sample(remaining, 6 - len(unique_team))

        if not self.meets_role_requirements(unique_team):
            # Fallback: brute-force search for a valid team up to 1000 attempts
            for _ in range(1000):
                candidate = self.random_team()
                if self.meets_role_requirements(candidate):
                    unique_team = candidate
                    break

        return unique_team
