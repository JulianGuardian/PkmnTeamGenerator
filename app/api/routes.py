from fastapi import APIRouter

from app.application.moveset_generator import generate_moveset
from app.application.role_assigner import assign_role
from app.application.team_generator import TeamGenerator
from app.domain.evaluator import explain_pokemon
from app.infraestructure.pokeapi_client import (
    get_full_pokemon,
    load_or_create_dataset,
    load_or_create_moves_dataset,
)
from app.schemas.pokemon_schema import (
    MoveSchema,
    ProfileSchema,
    PokemonSchema,
    StatsSchema,
    TeamResponse,
)

router = APIRouter()

dataset = None
moves_dataset = None


@router.on_event("startup")
def startup():
    global dataset, moves_dataset
    dataset = load_or_create_dataset(limit=1025)
    moves_dataset = load_or_create_moves_dataset(limit=937)


@router.get("/team", response_model=TeamResponse)
def generate_team():
    generator = TeamGenerator(dataset)
    best_team_basic = generator.evolve()

    full_team = [get_full_pokemon(p["name"]) for p in best_team_basic]

    response = []

    for p in full_team:
        stats = {
            "hp": p.hp,
            "attack": p.attack,
            "defense": p.defense,
            "special-attack": p.sp_attack,
            "special-defense": p.sp_defense,
            "speed": p.speed,
        }

        role = assign_role(stats)
        moves = generate_moveset(p, role, moves_dataset, full_team)

        response.append(
            PokemonSchema(
                name=p.name,
                sprite=p.sprite,
                types=p.types,
                ability=p.ability,
                ability_description=p.ability_description or None,
                stats=StatsSchema(
                    hp=p.hp,
                    attack=p.attack,
                    defense=p.defense,
                    sp_attack=p.sp_attack,
                    sp_defense=p.sp_defense,
                    speed=p.speed,
                ),
                moves=[
                    MoveSchema(
                        name=m["name"],
                        type=m["type"],
                        damage_class=m.get("damage_class") or None,
                        power=m.get("power") or None,
                        accuracy=m.get("accuracy") or None,
                        pp=m.get("pp") or None,
                        description=m.get("description") or None,
                    )
                    for m in moves
                ],
                profile=ProfileSchema(
                    role=role,
                    role_description=explain_pokemon(p, role),
                ),
            )
        )

    return TeamResponse(team=response)
