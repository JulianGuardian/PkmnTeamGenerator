# Pokémon Team Maker — Resumen del Proyecto

## Librerías utilizadas

| Librería | Propósito |
|---|---|
| **FastAPI** | Framework web que expone la API REST. Maneja el enrutamiento, el ciclo de vida de las peticiones/respuestas y la documentación automática en `/docs`. |
| **Uvicorn** | Servidor ASGI que ejecuta la aplicación FastAPI. |
| **Pydantic** | Validación y serialización de datos. Se usa para definir los esquemas de respuesta (`PokemonSchema`, `MoveSchema`, `ProfileSchema`, etc.) y garantizar que el JSON devuelto esté bien formado. |
| **Requests** | Cliente HTTP usado para llamar a PokéAPI durante la construcción de los datasets. |
| **json** | Módulo de la librería estándar usado para leer y escribir los archivos de dataset locales. |
| **os** | Módulo de la librería estándar usado para comprobar la existencia de archivos y construir rutas. |
| **random** | Módulo de la librería estándar usado en el algoritmo genético para la inicialización de equipos, mutación y selección. |
| **collections.Counter** | Usado para contar ocurrencias de roles, frecuencias de tipos y debilidades compartidas dentro de un equipo. |

---

## APIs utilizadas

### PokéAPI — `https://pokeapi.co/api/v2`

API REST gratuita, abierta y de solo lectura con datos de todos los juegos de Pokémon. No requiere autenticación.

La app llama a cinco endpoints durante la construcción del dataset:

| Endpoint | Para qué se usa |
|---|---|
| `GET /pokemon?limit=1025` | Obtener la lista de todos los nombres de Pokémon |
| `GET /pokemon/{name}` | Obtener tipos, estadísticas base, learnset, habilidad y sprite de cada Pokémon |
| `GET /pokemon-species/{name}` | Determinar si un Pokémon es legendario o mítico |
| `GET /move/{name}` | Obtener todos los datos mecánicos de cada movimiento (potencia, precisión, efectos, cambios de stats, etc.) |
| `GET /ability/{name}` | Obtener la descripción en inglés de la habilidad de un Pokémon |

Una vez guardados los datasets localmente, la API solo se vuelve a llamar cuando se genera un equipo — una vez por Pokémon para obtener la descripción de su habilidad (ya que ese campo no se almacena en el dataset).

---

## Cómo funciona el backend — resumen sencillo

1. **El servidor arranca** → comprueba si existen los dos archivos de dataset. Si no, descarga ~1025 Pokémon y ~950 movimientos de PokéAPI y los guarda como JSON. Esto solo ocurre una vez.

2. **El usuario llama a `GET /team`** → el backend ejecuta un algoritmo genético sobre el dataset de Pokémon para encontrar un equipo de 6 que puntúe bien en cobertura de tipos, diversidad de roles y balance de estadísticas.

3. **Para cada Pokémon del equipo**, el backend:
   - Obtiene sus datos completos (habilidad, sprite, learnset completo) desde PokéAPI o la caché local.
   - Le asigna un rol competitivo basado en sus estadísticas.
   - Selecciona 4 movimientos del dataset de movimientos, filtrando los malos y puntuando el resto.

4. **Devuelve una respuesta JSON** con los 6 Pokémon completamente descritos: tipos, estadísticas, habilidad (con descripción), 4 movimientos (con potencia, precisión, PP y descripción), y un perfil con el rol y una explicación escrita.

---

## ¿Qué machine learning se usa?

La aplicación usa un **algoritmo genético**, que se sitúa en una zona gris según el contexto:

- **En sentido estricto** (definición académica): los algoritmos genéticos pertenecen a la **computación evolutiva**, una subcategoría de la IA pero *no* del Machine Learning. ML se refiere específicamente a sistemas que aprenden un modelo a partir de datos — el algoritmo genético no tiene datos de entrenamiento, no tiene parámetros ajustables y nada persiste entre ejecuciones.
- **En sentido amplio** (uso en la industria): muchos programas de estudio y ofertas de trabajo agrupan los algoritmos genéticos dentro de "IA/ML" porque encuentran soluciones óptimas sin ser programados explícitamente. Llamarlo IA es correcto; llamarlo ML es una simplificación.

**La respuesta precisa para este proyecto: usa optimización basada en IA (computación evolutiva), no machine learning.**

Comparación con ML tradicional:

| | Algoritmo genético (esta app) | ML tradicional |
|---|---|---|
| Requiere datos de entrenamiento | No | Sí |
| Tiene parámetros aprendibles | No | Sí |
| Mejora con el tiempo | Sí, dentro de una ejecución | Sí, entre épocas de entrenamiento |
| Es determinista | No (mutaciones aleatorias) | Depende |
| Generaliza a nuevas entradas | No | Sí |

### Qué hace el algoritmo genético en esta app

Trata cada equipo candidato de 6 Pokémon como un **individuo** en una población. En cada **generación**:

- Los **20 equipos candidatos** son puntuados por una **función de fitness** que mide cobertura de tipos, diversidad de roles, sinergia defensiva y balance de estadísticas.
- Los **5 mejores equipos sobreviven** intactos (elitismo).
- Se crean **15 nuevos equipos** tomando un padre del top 10 y reemplazando aleatoriamente un Pokémon (mutación).
- Tras **20 generaciones**, se devuelve el equipo con mayor puntuación.

La función de fitness está completamente construida a mano basándose en conocimiento de Pokémon competitivo — no se aprende de datos. Las reglas de puntuación (ej. "+300 por tipo cubierto", "−800 por debilidad compartida con 4+ miembros") fueron diseñadas manualmente para reflejar qué hace a un equipo sólido.

### Qué se podría añadir con ML real

Si el proyecto se extendiera con machine learning, las posibles vías serían:

- **Aprendizaje por refuerzo** — entrenar un agente para construir equipos simulando batallas y premiando las victorias.
- **Función de fitness neuronal** — reemplazar la puntuación artesanal por un modelo entrenado con datos de equipos competitivos (ej. replays de Pokémon Showdown).
- **Modelo de recomendación de movimientos** — aprender qué movimientos son más efectivos para cada Pokémon a partir de estadísticas de uso en juego competitivo.
