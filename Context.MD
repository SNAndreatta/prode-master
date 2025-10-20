# 🏆 Prode App — Context

## Overview
Prode App is a football prediction (prode) platform where users can:
- Register and manage their accounts.
- Choose countries, leagues, and rounds.
- Predict match results (including penalties).
- Create and join tournaments with friends.
- View rankings and statistics globally or per tournament.

The project also includes administrative logic for managing data, metrics, and potentially premium features (like AI-generated predictions or analytics).

---

## ✅ Current Progress
### Completed
- **Endpoint:** `/rounds?league_id=n`
- **Endpoints:** `/tournaments` (`GET` and `POST`)
- **Tournament logic** (creation, visibility, linking to leagues)
- **Prediction logic**
- **Endpoints for predictions**
  - Get predictions
  - Send predictions

---

## 🧩 Planned Features
### User Features
- **Authentication**
  - Register, Login, Logout (token-based)
- **Profile**
  - Edit account (TBD)
- **Browse Leagues**
  - Select country → league → round
- **Predictions**
  - Predict goals (increment/decrement via + / - buttons)
  - Predict penalties
- **Tournaments**
  - Create and configure tournament
  - Invite users
- **Leaderboards**
  - Global and per-tournament standings

### Admin Features
- Access to user prediction metrics
- Manage leagues, teams, and tournaments
- Dashboard for insights and statistics

### Future / Optional
- AI-based predictions (via external football API)
- Payment or premium system for advanced features
- Buckets for media (team, league, and country images)

---

## 🧠 Models (Draft)
> These may evolve — tokens and “rounds” models pending.

- **User**
  - id, username, email, password_hash, country
- **League**
  - id, name, country_id, image_url
- **Round**
  - id, league_id, number, start_date, end_date
- **Match**
  - id, round_id, home_team_id, away_team_id, date
- **Prediction**
  - id, user_id, match_id, goals_home, goals_away, penalties_home, penalties_away
- **Tournament**
  - id, name, is_public, creator_id, participants, league_id
- **TournamentPrediction**
  - link between Tournament and Prediction

---

## ⚙️ Tech Stack
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL (Neon DB)
- **Authentication:** JWT / Tokens
- **Cache / Memory:** Valkey
- **Storage:** Buckets (for team/league images)
- **Frontend:** React + TypeScript + Vite

---

## 🚀 Potential Extensions
- **Admin Dashboard**
  - Metrics visualization
  - Tournament and user management
- **AI Prediction Service**
  - Fetch model-based predictions via football API
- **Premium Features**
  - Paid access to AI predictions or insights

---

## 🧭 API Examples
- `GET /rounds?league_id=5` → returns rounds for a specific league
- `GET /tournaments` → lists public tournaments
- `POST /tournaments` → creates a new tournament
- `GET /predictions` → fetch user predictions
- `POST /predictions` → submit or update predictions

---

## 🧑‍💻 Team Notes
- Complex logic will live server-side, not on the frontend.
- The UI should remain simple: clear, responsive, and intuitive.
- Admin and AI functionalities can be modular — integrated later.

