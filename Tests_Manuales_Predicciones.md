# Tests Manuales — Predicciones y Fixtures

Este documento recopila pruebas manuales paso a paso para las funcionalidades de `fixtures` (fixtures como la fuente única de partidos) y `predictions` (predicciones de usuarios). Incluye ejemplos de uso (curl), payloads, cabeceras, y respuestas esperadas.

Prerequisitos
- El servidor está corriendo (por defecto en http://127.0.0.1:8000).
- Base de datos inicializada (el `main` crea tablas en startup).
- Tener al menos un usuario con token JWT válido (se asume endpoint de auth ya existe).
- Existen fixtures cargados en la BD para los tests (véase "Cargar fixtures" más abajo).

Resumen de endpoints relevantes
- POST /predictions — Crear o actualizar predicción (auth required)
- GET /predictions — Obtener predicciones del usuario (auth required)
- DELETE /predictions/{match_id} — Eliminar predicción (auth required)
- GET /predictions/stats — Estadísticas del usuario (auth required)
- GET /predictions/match/{match_id} — Obtener predicciones para un match (auth required, comparte torneo)
- GET /admin/predictions/match/{match_id} — Obtener predicciones (admin)
- POST /admin/predictions/score — Calcular puntajes (admin)

Notas sobre fixtures
- El sistema usa el modelo `Fixture` como la fuente única de verdad.
- Las predicciones se validan contra el fixture: no se puede crear/editar/eliminar una predicción si el fixture está "locked" (comenzado o terminado).
- `FixturePostgres` expone helpers: `get_fixture_by_id`, `get_fixture_with_teams` y `_is_fixture_locked`.

Cómo obtener un token JWT (ejemplo)
1. Crear usuario (si tu API ofrece registro) o usar credenciales de prueba.
2. Obetener token via /auth/login (o similar).
Este documento asume que obtienes un token y lo pones en la variable SHELL `TOKEN`:

```bash
# ejemplo (ajusta según tu API de autenticación)
export TOKEN="eyJhbGci..."
```

A. Comprobar fixtures disponibles

1) Obtener todos los fixtures (si el endpoint existe)

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/fixtures
```

- Respuesta esperada: 200 OK con listado JSON de fixtures. Cada fixture contiene `id`, `league`, `home`, `away`, `date`, `status`, `round`, `home_team_score`, `away_team_score`, `home_pens_score`, `away_pens_score`.

2) Obtener fixture enriquecido (equipo incluido)

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/fixtures/{fixture_id}/with-teams
```

- Respuesta esperada: 200 OK con JSON enriquecido (ver fields en service `get_fixture_with_teams`).

B. Pruebas de Predicciones — flujo básico

1) Crear una predicción (POST /predictions)

- Payload de ejemplo:
```json
{
  "match_id": 123,
  "goals_home": 2,
  "goals_away": 1,
  "penalties_home": null,
  "penalties_away": null
}
```

- CURL:
```bash
curl -X POST http://127.0.0.1:8000/predictions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"match_id": 123, "goals_home": 2, "goals_away": 1}'
```

- Casos esperados:
  - Si el fixture `123` no existe: 400 con mensaje "Fixture with id 123 not found".
  - Si el fixture está locked (empezó o finalizó): 400 con mensaje "Cannot create prediction for a fixture that has started or finished".
  - Si la predicción se crea correctamente: 200 OK con el objeto `PredictionResponse` (id, user_id, match_id, goals, timestamps).

2) Actualizar la misma predicción: reusar el mismo endpoint POST (la lógica intenta actualizar si ya existe)

```bash
curl -X POST http://127.0.0.1:8000/predictions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"match_id": 123, "goals_home": 3, "goals_away": 1}'
```

- Respuesta esperada: 200 OK con la predicción actualizada (updated_at actualizado).

3) Obtener predicciones del usuario (GET /predictions)

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/predictions?match_id=123"
```

- Respuesta esperada: 200 OK, lista con la predicción para `match_id=123` con campo `match` embebido (según `PredictionWithMatch`).

4) Eliminar predicción (DELETE /predictions/{match_id})

```bash
curl -X DELETE http://127.0.0.1:8000/predictions/123 \
  -H "Authorization: Bearer $TOKEN"
```

- Casos esperados:
  - Si la predicción no existe: 404 Not Found.
  - Si el fixture está locked: 400 con mensaje "Cannot delete prediction for a fixture that has started or finished".
  - Si eliminado: 200 OK con JSON {"message": "Prediction deleted successfully", "match_id": 123}.

C. Estadísticas del usuario

1) Obtener estadísticas (GET /predictions/stats)

```bash
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/predictions/stats
```

- Respuesta esperada: 200 OK con objeto `PredictionStats`:
```json
{
  "total_predictions": 10,
  "correct_predictions": 3,
  "accuracy_percentage": 30.0,
  "average_goals_predicted": 2.1,
  "most_common_outcome": "win"
}
```

D. Ver predicciones de un partido (usuarios compartiendo torneo)

1) Obtener predicciones compartidas (GET /predictions/match/{match_id})

```bash
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/predictions/match/123
```

- Respuesta esperada: 200 OK con lista `PredictionResponse` de usuarios que comparten torneo (o vacía si ninguno).

E. Endpoints administrativos

> Nota: admin check no implementado; estos endpoints requieren que `get_current_user` obtenga un admin o se omita la verificación durante pruebas.

1) Obtener todas las predicciones de un match (admin)

```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://127.0.0.1:8000/admin/predictions/match/123
```

- Respuesta esperada: 200 OK con `AdminPredictionResponse[]` (incluye username de cada usuario).

2) Calcular puntajes para un match (POST /admin/predictions/score)

```bash
curl -X POST http://127.0.0.1:8000/admin/predictions/score \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"match_id": 123, "exact_score_points": 10, "correct_winner_points": 5, "penalty_bonus_points": 3}'
```

- Respuesta esperada: 200 OK con `ScoreCalculationResponse`:
```json
{
  "match_id": 123,
  "total_predictions": 5,
  "scores_calculated": 5,
  "exact_scores": 1,
  "correct_winners": 3,
  "penalty_bonuses": 0
}
```

F. Tests de fixtures (actualizado)

1) Crear/actualizar fixture vía servicio (no hay endpoint público en esta API por defecto — se muestran ejemplos directos contra DB/service si quieres crear endpoints)

Si necesitas cargar fixtures de prueba rápidamente, puedes usar el script de administración o crear una ruta temporal en `blueprints` que invoque `FixturePostgres.add_or_update_fixture`.

Ejemplo (sugerido script/temporario):

```python
# script para cargar fixture de ejemplo (ejecutar en contexto de app con db)
from services.fixture_postgres import FixturePostgres
from database import get_db

async def create_sample_fixture():
    async with get_db() as db:
        svc = FixturePostgres()
        await svc.add_or_update_fixture(db, id=123, league_id=1, home_id=10, away_id=20, date=datetime.utcnow(), home_team_score=None, away_team_score=None, home_pens_score=None, away_pens_score=None, status=FixtureStatus.SCHEDULED, round="Group A")
```

G. Casos límite y errores esperados
- Intentar predecir un fixture inexistente → 400
- Intentar predecir después de que el fixture inició/terminó → 400
- Intentar crear duplicado de predicción → 400
- Intentar eliminar predicción inexistente → 404

H. Notas de implementación y mapeo de campos
- El `Prediction` usa `match_id` que mapea al `Fixture.id`.
- `Fixture` fields: id, league_id, home_id, away_id, date, home_team_score, away_team_score, home_pens_score, away_pens_score, status, round.
- `PredictionWithMatch` y `MatchResponse` en schemas transforman nombres internos para consistencia en la API.

I. Checklist rápido para ejecutar las pruebas
- [ ] Ejecutar servidor: `env/bin/python -m uvicorn main:app --reload --port 8000`
- [ ] Exportar token: `export TOKEN="<tu_jwt>"`
- [ ] Asegurar fixtures de prueba (crear con script o endpoint)
- [ ] Ejecutar CURLs arriba en orden: crear -> obtener -> actualizar -> stats -> eliminar


---
Si quieres, puedo:
- Añadir scripts de carga de fixtures y usuarios de prueba en `scripts/`.
- Implementar endpoints temporales para crear fixtures desde HTTP (útil para pruebas manuales).
- Ejecutar los CURLs aquí y reportar los resultados en vivo (necesitaré un token válido o crear usuarios de prueba).

¿Qué prefieres que haga ahora?