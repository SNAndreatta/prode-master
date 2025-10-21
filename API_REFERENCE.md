# API Reference — Prode App

About This API Reference Page

This document is the official API reference for the Prode App, a football prediction platform. It is intended for developers, frontend engineers, and integrators who need a complete overview of all public and authenticated API endpoints, how to use them, and what data to expect.

Purpose of this page:

Provide a centralized reference for all backend endpoints.

Explain how each endpoint works, what data it requires, and what it returns.

Clarify authentication and authorization requirements for protected routes.

Serve as a guide for frontend development, including example requests, responses, and notes for UI behavior.

How to use this page:

Follow the example curl commands or translate them to your preferred HTTP client (Axios, fetch, Postman, etc.).

Use the response schemas to structure frontend components, forms, and state management.

Implement error handling according to the HTTP status codes and messages described.

Observe the prediction lifecycle rules, tournament participation logic, and fixture constraints when building user interfaces.

Reference the sections on authentication, predictions, fixtures, leagues, rounds, and tournaments to understand how the app’s flows are connected.

Intended audience:

Frontend developers integrating the API with React/TypeScript/Vite.

Backend engineers maintaining or extending endpoints.

QA engineers testing API flows.

Designers or product managers reviewing feature behavior before implementation.

Outcome of using this page:
By following this API reference, a developer or integrator can:

Fully implement prediction creation, viewing, updating, and deletion.

Manage user authentication and session handling.

Display and interact with fixtures, rounds, leagues, and tournaments.

Ensure correct handling of business rules, such as locked predictions, tournament joins/leaves, and admin-only actions.

Avoid inconsistencies between the frontend and backend by following the data shapes and validation rules outlined here.

This document lists all public API endpoints and authentication endpoints implemented in the codebase. Each endpoint includes: HTTP method, route, short description, required headers/auth, example requests (curl), and expected frontend response shape.

Note: replace `http://127.0.0.1:8000` with your deployment URL.

---

## Authentication (Auth)

### POST /auth/register
- Purpose: Create a new user account
- Auth: none
- Request body (JSON):
```json
{
  "email": "alice@example.com",
  "username": "alice",
  "password": "secret"
}
```
- Example curl:
```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","username":"alice","password":"secret"}'
```
- Successful response: 200 OK
```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com"
}
```
- Frontend notes: store `id` and `username`; next step usually a login for tokens.

---

### POST /auth/login
- Purpose: Exchange credentials for JWT access and refresh tokens
- Auth: none
- Request body (JSON):
```json
{
  "email": "alice@example.com",
  "password": "secret"
}
```
- Example curl:
```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"secret"}'
```
- Successful response: 200 OK
```json
{
  "access_token": "<JWT_ACCESS>",
  "refresh_token": "<JWT_REFRESH>",
  "token_type": "bearer"
}
```
- Frontend notes: store access token in memory or secure storage; use Authorization header: `Authorization: Bearer <access_token>` for protected endpoints. Keep refresh token secure (used to refresh access token).

---

### POST /auth/refresh
- Purpose: Use refresh token to obtain a new access token
- Auth: none (but accepts refresh token in body)
- Request body:
```json
{"refresh_token":"<JWT_REFRESH>"}
```
- Example curl:
```bash
curl -X POST http://127.0.0.1:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<JWT_REFRESH>"}'
```
- Successful response: 200 OK
```json
{
  "access_token": "<NEW_ACCESS>",
  "refresh_token": "<JWT_REFRESH>",
  "token_type": "bearer"
}
```

---

### POST /auth/logout
- Purpose: Revoke a refresh token (logout)
- Auth: none (accepts refresh token in body)
- Request body:
```json
{"refresh_token":"<JWT_REFRESH>"}
```
- Example curl:
```bash
curl -X POST http://127.0.0.1:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<JWT_REFRESH>"}'
```
- Successful response: 200 OK
```json
{"detail": "Sesión cerrada correctamente"}
```

---

## Predictions API
All prediction endpoints require the Authorization header:
```
Authorization: Bearer <ACCESS_TOKEN>
```

Schemas referenced (summary):
- `PredictionCreate`: { match_id, goals_home, goals_away, penalties_home?, penalties_away? }
- `PredictionResponse`: { id, user_id, match_id, goals_home, goals_away, penalties_home?, penalties_away?, created_at, updated_at }
- `PredictionWithMatch`: `PredictionResponse` + `match` object

### POST /predictions
- Purpose: Create or update a prediction for a fixture (if exists, will update)
- Auth: Required
- Request body:
```json
{
  "match_id": 123,
  "goals_home": 2,
  "goals_away": 1,
  "penalties_home": null,
  "penalties_away": null
}
```
- Example curl:
```bash
curl -X POST http://127.0.0.1:8000/predictions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"match_id":123,"goals_home":2,"goals_away":1}'
```
- Success: 200 OK with `PredictionResponse`:
```json
{
  "id": 42,
  "user_id": 4,
  "match_id": 123,
  "goals_home": 2,
  "goals_away": 1,
  "penalties_home": null,
  "penalties_away": null,
  "created_at": "2025-10-20T12:00:00",
  "updated_at": "2025-10-20T12:00:00"
}
```
- Error cases to handle in frontend:
  - 400: Fixture not found or fixture locked
  - 500: server error (e.g., DB constraint issues)

### GET /predictions
- Purpose: Retrieve current user's predictions; supports filters
- Query params: `match_id` (optional), `round_id` (optional), `league_id` (optional)
- Auth: Required
- Example:
```bash
curl -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8000/predictions?match_id=123"
```
- Success: 200 OK — List of `PredictionWithMatch` objects. Example single item:
```json
[{
  "id": 42,
  "user_id": 4,
  "match_id": 123,
  "goals_home": 2,
  "goals_away": 1,
  "penalties_home": null,
  "penalties_away": null,
  "created_at": "2025-10-20T12:00:00",
  "updated_at": "2025-10-20T12:00:00",
  "match": {
    "id": 123,
    "round_id": 11,
    "home_team_id": 10,
    "away_team_id": 20,
    "start_time": "2025-10-21T18:00:00",
    "finished": false,
    "result_goals_home": null,
    "result_goals_away": null,
    "result_penalties_home": null,
    "result_penalties_away": null
  }
}]
```

### DELETE /predictions/{match_id}
- Purpose: Delete current user's prediction for a specific match
- Auth: Required
- Example:
```bash
curl -X DELETE http://127.0.0.1:8000/predictions/123 \
  -H "Authorization: Bearer $TOKEN"
```
- Successful response: 200 OK
```json
{"message":"Prediction deleted successfully","match_id":123}
```
- Error cases: 400 if fixture locked; 404 if prediction not found

### GET /predictions/stats
- Purpose: Get aggregated statistics for user predictions
- Auth: Required
- Example:
```bash
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/predictions/stats
```
- Success: 200 OK — `PredictionStats`:
```json
{
  "total_predictions": 10,
  "correct_predictions": 3,
  "accuracy_percentage": 30.0,
  "average_goals_predicted": 2.1,
  "most_common_outcome": "win"
}
```

### GET /predictions/match/{match_id}
- Purpose: Get predictions for a match visible to the current user (only users who share a tournament)
- Auth: Required
- Example:
```bash
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/predictions/match/123
```
- Success: 200 OK — List of `PredictionResponse` objects

---

## Admin Predictions API
Note: admin role checks are TODO; endpoints exist and require authentication. Frontend should only expose to admin users.

### GET /admin/predictions/match/{match_id}
- Purpose: Retrieve all predictions for a match (no tournament filtering)
- Auth: Required (admin)
- Example:
```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://127.0.0.1:8000/admin/predictions/match/123
```
- Success: 200 OK — List of `AdminPredictionResponse` objects (includes username & match details)

### POST /admin/predictions/score
- Purpose: Calculate scores for all predictions of a match
- Auth: Required (admin)
- Request body:
```json
{
  "match_id": 123,
  "exact_score_points": 10,
  "correct_winner_points": 5,
  "penalty_bonus_points": 3
}
```
- Example curl:
```bash
curl -X POST http://127.0.0.1:8000/admin/predictions/score \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"match_id":123}'
```
- Success: 200 OK — returns `ScoreCalculationResponse`:
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

---

## Fixtures, Leagues & Rounds
These endpoints are used by the frontend to browse leagues, rounds, and fixtures.

### GET /fixtures
- Purpose: Get fixtures by league and round (uses valkey + DB for enriched data)
- Query params: `league_id` (required), `round_name` (required)
- Example:
```bash
curl -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8000/fixtures?league_id=39&round_name=Regular%20Season%20-%2010"
```
- Successful response: 200 OK JSON with structure:
```json
{
  "status": "success",
  "league": { /* league object */ },
  "round": { /* round object */ },
  "fixtures": [ /* list of enriched fixtures */ ]
}
```
- `fixtures` entries include: id, league, home, away, date (ISO), home_team_score, away_team_score, home_pens_score, away_pens_score, status, round

### GET /rounds/by-league
- Purpose: Get all rounds for a league
- Query params: `league_id` (required), `season` (optional)
- Example:
```bash
curl "http://127.0.0.1:8000/rounds/by-league?league_id=39&season=2023"
```
- Success: 200 OK
```json
{ "status":"success", "league":{...}, "rounds": [...], "count": 38 }
```

### GET /leagues
- Purpose: Get leagues for a country (query param `country_name` required)
- Example:
```bash
curl "http://127.0.0.1:8000/leagues?country_name=Argentina"
```
- Success: 200 OK — { status, country, leagues }

---

## Tournaments
Tournaments endpoints exist for public browsing and CRUD operations; many are auth-protected.

### GET /tournaments
- Purpose: Get public tournaments (optional filter by `league_id`)
- Example:
```bash
curl "http://127.0.0.1:8000/tournaments"
```
- Success: 200 OK — list of tournaments

### POST /tournaments
- Purpose: Create a new tournament (auth required)
- Request body:
```json
{
  "name":"My Office Pool",
  "description":"Friendly tournament",
  "league_id": 39,
  "is_public": true,
  "max_participants": 100
}
```
- Response: TournamentResponse object

### POST /tournaments/{id}/join
- Purpose: Join a tournament (auth required)
- Response: confirmation object with `tournament_id` and `user_id`

### DELETE /tournaments/{id}/leave
- Purpose: Leave a tournament (auth required)

And many more endpoints under `tournaments.py` for management and participant handling (see file for details).

---

## Notes for frontend integrators
- Authentication: always include `Authorization: Bearer <access_token>` header for protected routes.
- Error handling: endpoints use HTTP status codes and JSON `detail` or structured responses. Example:
  - 400 Bad Request — validation or business rule (e.g., fixture locked)
  - 401 Unauthorized — invalid or missing token
  - 403 Forbidden — operations not allowed (e.g., not creator/admin)
  - 404 Not Found — resource missing
  - 500 Internal Server Error — server-side
- Date format: ISO-8601 strings (UTC), e.g., `2025-10-20T12:00:00`
- Prediction lifecycle:
  - Create/update via POST /predictions; delete via DELETE /predictions/{match_id}.
  - Predictions are time-locked. The frontend should disable prediction inputs when fixture `date` is in the past or fixture `status` is finished.

---

# Frontend specifications
- Notification system for error handling where every error is displayed on bottom left
- Add loading animations to every fetch to the Api for visual reference
- Add animations to enhance user expeperience such as: Confirmation button (like sliding when something is succesfull or progressing, or animating from bottom to its position when first loaded home, etc)
- Make black and white desing with dark theme
- I need the following pages and components: Header with link to home and login and singup buttons in header and forms as pop ups for these, and then the header when the user is logged the header updates to showing your username and logout. I need a simple footer. The page is called prode master and the logo is a ball. Home page a way to access to the pages which are: predictions and tournaments. The tournaments page should have eveything included in the endpoints and the prediction page should let the user choose from countries with league, then with league, then round and then the fixtures should be displayed on a way that the teams are shown, and if the match has ended show the result and how many points the user got from his prediction. The prediction can be changed with + and - buttons or via text. The user should be able to update all its predictions with a button which would send a post prediction for every fixture in the round he's updating its predictions. Consider these states for matches:
    TBD = "Time To Be Defined"
    NS = "Not Started"
    H1 = "First Half, Kick Off"
    HT = "Halftime"
    H2 = "Second Half, 2nd Half Started"
    ET = "Extra Time"
    BT = "Break Time"
    P = "Penalty In Progress"
    SUSP = "Match Suspended"
    INT = "Match Interrupted"
    FT = "Match Finished"
    AET = "Match Finished After Extra Time"
    PEN = "Match Finished After Penalty Shootout"
    PST = "Match Postponed"
    CANC = "Match Cancelled"
    ABD = "Match Abandoned"
    AWD = "Technical Loss"
    WO = "WalkOver"
    LIVE = "In Progress"
- I want you to make auth handling in frontend when using login and singup forms that store tokens in local storage.
- Use shadcn component, tailwind, React Vite and TypeScript
