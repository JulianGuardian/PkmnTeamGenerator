from typing import List, Optional

from pydantic import BaseModel


class MoveSchema(BaseModel):
    name: str
    type: str
    damage_class: Optional[str] = None
    power: Optional[int] = None
    accuracy: Optional[int] = None
    pp: Optional[int] = None
    description: Optional[str] = None


class StatsSchema(BaseModel):
    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int


class ProfileSchema(BaseModel):
    role: str
    role_description: str


class PokemonSchema(BaseModel):
    name: str
    sprite: str
    types: List[str]
    ability: str
    ability_description: Optional[str] = None
    stats: StatsSchema
    moves: List[MoveSchema]
    profile: ProfileSchema


class TeamResponse(BaseModel):
    team: List[PokemonSchema]
