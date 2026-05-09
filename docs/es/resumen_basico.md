# Pokémon Team Maker — Resumen Básico / Intermedio

## ¿Qué hace la aplicación?

Genera un equipo competitivo de 6 Pokémon, cada uno con 4 movimientos, diseñados para funcionar bien juntos. El equipo cubre una amplia variedad de tipos tanto ofensiva como defensivamente, e incluye un conjunto diverso de roles de batalla.

---

## ¿De dónde vienen los datos?

La aplicación descarga datos de **PokéAPI**, una API pública y gratuita que contiene información sobre todos los Pokémon y movimientos de los juegos.

Se guardan dos archivos JSON localmente para evitar descargar todo cada vez:

| Archivo | Contenido |
|---|---|
| `data/pokemon_dataset.json` | Nombre, tipos, estadísticas y estado legendario de ~1025 Pokémon |
| `data/moves_dataset.json` | Nombre, tipo, potencia, precisión, efectos y mecánicas de ~950 movimientos |

Ambos archivos están incluidos en el repositorio, por lo que no se necesita ninguna descarga al iniciar. Si se eliminaran, la app los volvería a descargar desde la API automáticamente al arrancar el servidor.

---

## ¿Cómo se construye el equipo?

El equipo se construye en dos etapas:

### Etapa 1 — Elegir los 6 Pokémon

La aplicación usa un **algoritmo genético** — una técnica de optimización inspirada en la selección natural — para encontrar la mejor combinación de 6 Pokémon.

Funciona así:

1. **Crea una población aleatoria** de 20 equipos candidatos.
2. **Puntúa cada equipo** según qué tan bueno es (cobertura de tipos, diversidad de roles, balance de estadísticas).
3. **Conserva los 5 mejores equipos** y genera 15 nuevos mutando levemente (cambiando un Pokémon) a partir de los 10 mejores.
4. **Repite durante 20 generaciones.**
5. **Devuelve el mejor equipo** encontrado en todas las generaciones.

Los equipos se puntúan por cosas como:
- Cuántos de los 18 tipos pueden golpear con superefectividad
- Cuántos roles de batalla diferentes están representados
- Si varios Pokémon comparten la misma debilidad de tipo

### Etapa 2 — Asignar 4 movimientos a cada Pokémon

Una vez seleccionados los 6 Pokémon, a cada uno se le asigna un **rol** según sus estadísticas:

| Rol | Descripción |
|---|---|
| `physical_sweeper` | Alto ataque físico — se enfoca en hacer daño |
| `special_sweeper` | Alto ataque especial — se enfoca en hacer daño |
| `revenge_killer` | Muy rápido — entra a eliminar rivales debilitados |
| `annoyer` | Alto bulk — usa movimientos de estado para desgastar |
| `tank` | Alto bulk — absorbe golpes y devuelve daño sostenido |
| `balanced` | Sin estadísticas extremas — perfil flexible y versátil |

Luego la app selecciona 4 movimientos para cada Pokémon usando los siguientes criterios:

- **Movimientos STAB** (mismo tipo que el Pokémon) para daño confiable
- **Movimientos de cobertura** que golpeen tipos que el resto del equipo no puede cubrir
- **Movimientos de setup** apropiados para el rol (ej. Danza Espada para sweepers físicos)
- **Movimientos de recuperación, estado o utilidad** para annoyers y tanks

Los movimientos malos o situacionales se filtran — cosas como movimientos de dos turnos (Rayo Solar), movimientos suicidas (Explosión), movimientos de muy baja precisión, o movimientos que solo sirven en batallas dobles.

---

## ¿Cómo se devuelve el resultado?

La aplicación expone un único endpoint REST:

```
GET /team
```

Devuelve un JSON con 6 Pokémon. Cada uno incluye:

- Nombre, URL del sprite, tipos
- Nombre y descripción de la habilidad
- Estadísticas (PS, Ataque, Defensa, At. Esp., Def. Esp., Velocidad)
- 4 movimientos, cada uno con nombre, tipo, categoría, potencia, precisión, PP y descripción
- Un objeto `profile` con el rol asignado y una explicación escrita del por qué

---

## Reglas y restricciones

- **Máximo 1 legendario** por equipo (opcional — el equipo puede tener cero).
- **BST mínimo de 450** — los Pokémon muy débiles quedan excluidos.
- **No más de 2 Pokémon** con el mismo tipo primario.
- **Debe cubrir al menos 10 de los 18 tipos** ofensivamente.
- **Debe tener los 4 roles obligatorios**: sweeper físico, sweeper especial, revenge killer y annoyer, más al menos un tank o balanced.

---

## Flujo resumido

```
Inicia el servidor
       │
       ▼
Carga / descarga los datasets
       │
       ▼
Llega petición GET /team
       │
       ▼
Algoritmo genético selecciona 6 Pokémon
       │
       ▼
A cada Pokémon se le asigna un rol
       │
       ▼
A cada Pokémon se le seleccionan 4 movimientos
       │
       ▼
Se devuelve la respuesta JSON
```
