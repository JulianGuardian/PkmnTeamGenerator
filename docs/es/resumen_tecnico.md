# Pokémon Team Maker — Resumen Técnico Intermedio / Avanzado

## Arquitectura

```
app/
├── api/
│   └── routes.py              # Router de FastAPI, evento startup, endpoint /team
├── application/
│   ├── team_generator.py      # Algoritmo genético — selecciona 6 Pokémon
│   ├── team_evaluator.py      # Función de fitness — puntúa un equipo candidato
│   ├── role_assigner.py       # Asigna un rol competitivo a partir de las stats
│   ├── moveset_generator.py   # Selecciona 4 movimientos por Pokémon
│   └── type_coverage.py       # Motor de efectividad de tipos
├── domain/
│   ├── models.py              # Dataclass Pokemon
│   └── evaluator.py           # Descripciones de roles y explain_pokemon()
├── infraestructure/
│   └── pokeapi_client.py      # Llamadas a la API y gestión de datasets
└── schemas/
    └── pokemon_schema.py      # Modelos de respuesta con Pydantic
```

---

## Capa de datos

### Construcción de datasets (`pokeapi_client.py`)

Se construyen dos datasets en el primer arranque y se persisten como JSON:

**`pokemon_dataset.json`** — registro ligero por Pokémon:
```json
{ "name": "garchomp", "types": ["dragon","ground"], "stats": {...}, "is_legendary": false }
```

**`moves_dataset.json`** — registro completo por movimiento:
```json
{
  "name": "earthquake", "type": "ground", "damage_class": "physical",
  "power": 100, "accuracy": 100, "priority": 0, "pp": 10,
  "target": "all-other-pokemon",
  "recoil": 0, "drain": 0, "healing": 0,
  "ailment": "none", "ailment_chance": 0, "flinch_chance": 0,
  "stat_chance": 0, "crit_rate": 0, "min_hits": null, "max_hits": null,
  "effect_short": "...", "description": "...", "meta_category": "damage",
  "min_turns": null, "max_turns": null,
  "user_stat_drops": {}, "user_stat_boosts": {}, "enemy_stat_drops": {}
}
```

#### Lógica de clasificación de cambios de estadísticas

El array `stat_changes` de la API no indica explícitamente si el cambio afecta al usuario o al rival. El cliente lo reconstruye a partir de tres campos: `target_name`, `damage_class` y `stat_chance`:

```
change > 0 AND target == "user"                     → user_stat_boosts   (Danza Espada)
change < 0 AND damage_class == "status"
    AND target in rivales                            → enemy_stat_drops   (Encanto, Chillido)
    AND target == "user"                             → user_stat_drops    (Alma Clangora)
change < 0 AND damage_class != "status"
    AND 0 < stat_chance < 100                        → enemy_stat_drops   (Mordisco 20%)
    AND stat_chance == 100 OR stat_chance == 0       → user_stat_drops    (Combate, Hoja Aguda)
```

Clave: `stat_chance == 100` en un movimiento ofensivo significa penalización garantizada al propio usuario (como Combate), no un efecto secundario sobre el rival.

---

## Motor de tipos (`type_coverage.py`)

Cargado desde `data/type_chart.json` — tabla de consulta preconstruida con `strengths`, `weaknesses` e `immunes` por tipo.

Funciones principales:

| Función | Descripción |
|---|---|
| `type_effectiveness(atk, def_types)` | Devuelve el multiplicador de daño (0, 0.25, 0.5, 1, 2, 4) |
| `offensive_coverage(types)` | Conjunto de tipos golpeados con superefectividad por el STAB del Pokémon |
| `move_coverage(move_type)` | Conjunto de tipos golpeados con superefectividad por un movimiento |
| `pokemon_weaknesses(types)` | Todos los tipos que hacen ≥2x a este Pokémon |
| `pokemon_resistances(types)` | Todos los tipos que hacen ≤0.5x |
| `team_offensive_coverage(team)` | Unión de coberturas ofensivas de los 6 miembros |
| `team_defensive_weaknesses(team)` | Contador de cuántos miembros comparten cada debilidad |
| `type_synergy_score(team)` | +50 por cada par donde un miembro resiste la debilidad de otro |

---

## Algoritmo genético (`team_generator.py`)

### Población y selección

```python
population = [random_team() for _ in range(20)]  # 20 equipos aleatorios

for generation in range(20):
    population.sort(key=fitness, reverse=True)
    next_gen = population[:5]                     # elitismo: conservar top 5

    while len(next_gen) < 20:
        parent = random.choice(population[:10])   # selección del top 10
        child = mutate(parent)                    # reemplazar 1 Pokémon aleatorio
        next_gen.append(child)

    population = next_gen
```

### Restricciones de mutación

- No puede haber nombres de Pokémon duplicados en el equipo.
- Si el equipo ya tiene 1 legendario, el slot mutado debe ser no-legendario.

### Función de fitness (`team_evaluator.py`)

```
score = 0

+ len(tipos cubiertos con superefectividad) × 300
+ 2000 si se cubren ≥15 tipos, +1000 si ≥12

- count × 800 si una debilidad de tipo es compartida por ≥4 miembros
- count × 300 si ≥3 miembros comparten una debilidad
- count × 50  si 2 miembros comparten una debilidad

+ type_synergy_score(team)           # cobertura de resistencias entre pares

- (count - 2) × 500 por cada tipo que aparece ≥3 veces

+ 400 si ≥2 atacantes físicos (atk > 100)
+ 400 si ≥2 atacantes especiales (spa > 100)
+ 500 si hay al menos 1 de cada (ataque mixto)
+ 300 si ≥2 miembros rápidos (speed > 100)
+ 300 si ≥1 miembro bulky (PS × (def+spdef)/2 > 14000)
```

Además, `role_diversity_bonus()` añade ±1000/±10000 según la presencia de roles:

```python
required = ["annoyer", "revenge_killer", "physical_sweeper", "special_sweeper"]
# +1000 por cada rol presente, -10000 por cada rol ausente
# +1000 si tank >= 2 O (tank >= 1 Y balanced >= 1), si no -10000
```

### Restricciones duras (`meets_role_requirements`)

Tras la evolución, el equipo ganador debe cumplir todo esto o el algoritmo recurre a búsqueda aleatoria por fuerza bruta (hasta 1000 intentos):

- Los 4 roles obligatorios presentes
- Al menos 1 tank o balanced
- Ningún tipo primario aparece 3+ veces
- Cobertura ofensiva ≥ 10 tipos

---

## Asignación de roles (`role_assigner.py`)

Clasificación puramente basada en estadísticas. Se aplica tanto a Pokémon del dataset (dict) como a objetos Pokémon completos:

```python
bulk = ps * (defensa + def_especial) / 2

is_wall = bulk > 18000 O (defensa > 130 Y def_esp > 100 Y velocidad < 60)
if is_wall Y velocidad < 80  → "annoyer"
elif velocidad > 120         → "revenge_killer"
elif ataque > 120            → "physical_sweeper"
elif at_especial > 120       → "special_sweeper"
elif bulk > 15000            → "tank"
else                         → "balanced"
```

---

## Generador de movimientos (`moveset_generator.py`)

### Pipeline de filtrado

Cada movimiento pasa por un filtro secuencial:

1. Debe estar en el learnset del Pokémon
2. No estar en `BANNED_MOVES` ni en `LOW_QUALITY_MOVES`
3. El target no debe estar en `DOUBLES_ONLY_TARGETS`
4. `recoil` no ≤ −33 (retroceso fuerte), no ≤ −100 (noqueo)
5. `is_charge_move`: `effect_short` no debe contener "recharge", "next turn" ni "second turn"
6. `is_lockin_move`: `min_turns ≥ 2` O `"confused after"` en `effect_short`
7. `self_debuffs_main_attack`: `user_stat_drops` en ataque/at_especial ≤ −2
8. `rest`: solo permitido si `PS × (def + def_esp) / 2 ≥ 12000`
9. `accuracy` ≥ 70
10. `trick-room`: solo si la velocidad media del equipo ≤ 90
11. Categoría de daño dominante: si `|ataque − at_especial| > 20`, filtrar movimientos de la categoría opuesta
12. Umbral mínimo de stat: movimientos físicos filtrados si `ataque < 40`; especiales si `at_especial < 40`

### Categoría de daño preferida

```python
diff = pokemon.attack - pokemon.sp_attack
if diff > 20  → "physical"
if diff < -20 → "special"
else          → None  (mixto)
```

### Puntuación (`score_move`)

Cada movimiento válido recibe una puntuación competitiva:

```
puntuación_base = potencia + (precisión − 70) × 0.5
               − (50 − potencia) × 2  si potencia < 50  (penalización por potencia baja)

+ 30     si STAB
+ 80 × n si el movimiento cubre n tipos que el equipo no cubre
+ 50/25  si prioridad ≥ 2 / == 1
+ 20 × crit_rate
+ ailment_chance × 0.3 + flinch_chance × 0.2 + stat_chance × 0.2
+ 20     si movimiento de drenaje
+ suma(|enemy_stat_drops|) × 15
+ 20 + total_user_boosts × 8  si movimiento de setup
+ 35     si movimiento de recuperación
+ 40     si movimiento pivote (U-turn, Volt Switch, etc.)
+ UTILITY_BONUS[nombre]  (stealth-rock=50, defog=50, taunt=50, knock-off=40…)
+ META_BONUS[nombre]     (earthquake=40, ice-beam=35, moonblast=35…)
```

### Selección de movimientos por rol (`pick_role_moves`)

Tras la puntuación, cada rol tiene una plantilla específica:

| Rol | Slot 1 | Slot 2 | Slot 3 | Slot 4 |
|---|---|---|---|---|
| physical_sweeper | Mejor STAB | 2.º mejor STAB | Mejor cobertura | Setup físico (o más cobertura) |
| special_sweeper | Mejor STAB | 2.º mejor STAB | Mejor cobertura | Setup especial (o más cobertura) |
| revenge_killer | Movimiento de prioridad | Mejor STAB | 2.º STAB | Pivote / cobertura |
| annoyer | Debuff al rival | Estado de problema | Setup defensivo | Recuperación |
| tank | Mejor STAB | Movimiento de drenaje | Setup defensivo | Recuperación |
| balanced | Mejor STAB | Mejor cobertura | Setup (según stat dominante) | Utilidad |

Tras la selección por rol, `complete_moveset()` rellena los slots restantes de forma greedy por puntuación, priorizando cobertura de tipos y evitando tipos de movimiento duplicados.

Una garantía final asegura que siempre haya al menos 1 movimiento dañino.

### Conciencia de cobertura

El moveset de cada Pokémon se calcula con conocimiento de lo que el resto del equipo ya cubre:

```python
team_covered    = unión de offensive_coverage(p.types) de todos los compañeros
uncovered_types = LOS_18_TIPOS − team_covered
```

La puntuación de cobertura recibe `+80 × (tipos recién cubiertos)`, empujando al algoritmo a llenar huecos en vez de duplicar lo que los compañeros ya cubren.

---

## Esquema de respuesta

```
PokemonSchema
├── name: str
├── sprite: str (URL)
├── types: List[str]
├── ability: str
├── ability_description: str | null
├── stats: StatsSchema {hp, attack, defense, sp_attack, sp_defense, speed}
├── moves: List[MoveSchema]
│   └── MoveSchema
│       ├── name: str
│       ├── type: str
│       ├── damage_class: str | null       ("physical", "special", "status")
│       ├── power: int | null              (null para movimientos de estado)
│       ├── accuracy: int | null           (null para movimientos que nunca fallan)
│       ├── pp: int | null
│       └── description: str | null
└── profile: ProfileSchema
    ├── role: str
    └── role_description: str
```
