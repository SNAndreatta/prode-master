import logging
import requests
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from core.api_connection.connection import apiFutbolServicio
from services.teams.teams_postgres import TeamPostgres
from services.country.country_postgres import CountryPostgres
from services.leagues.leagues_postgres import LeaguePostgres  # Import LeaguePostgres
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger("teams_logger")
logger.setLevel(logging.INFO)

api_endpoint = os.getenv("API_ENDPOINT")

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

teams_router = APIRouter()

@teams_router.get("/api/teams")
async def get_teams(db: AsyncSession = Depends(get_db)):
    apiFutbol = apiFutbolServicio(endpoint=api_endpoint)
    team_postgres = TeamPostgres()
    league_postgres = LeaguePostgres()  # Initialize LeaguePostgres
    country_postgres = CountryPostgres()

    logger.info("Fetching teams from external API...")

    try:
        # Fetch all leagues from the database
        leagues = await league_postgres.get_all_leagues(db)
        logger.info(f"Retrieved {len(leagues)} leagues from the database.")

        added_count = 0
        failed_count = 0
        failed_teams = []

        for league in leagues:
            logger.info(f"Fetching teams for league: {league.name}")

            respuesta = None
            # Intentar primero con temporada 2025
            try:
                respuesta = apiFutbol.Equipos(liga=league.name, season=2025)
                logger.info(f"Received {len(respuesta)} teams for {league.name} season 2025.")
            except requests.HTTPError as e:
                logger.warning(f"No data for {league.name} season 2025: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error for {league.name} season 2025: {e}")

            if not respuesta:
                try:
                    respuesta = apiFutbol.Equipos(liga=league.name, season=2026)
                    logger.info(f"Received {len(respuesta)} teams for {league.name} season 2026.")
                except requests.HTTPError as e:
                    logger.warning(f"No data for {league.name} season 2026: {e}")
                except Exception as e:
                    logger.warning(f"Unexpected error for {league.name} season 2026: {e}")

            if not respuesta:
                logger.warning(f"Skipping league {league.name} because no teams were found for seasons 2025 or 2026.")
                continue

            # Aquí seguís con tu loop para agregar los equipos
            for item in respuesta:
                try:
                    team_data = item.get("team", {})
                    country_data = item.get("country", {})

                    team_id = team_data.get("id")
                    team_name = team_data.get("name", "Unknown Team")
                    team_logo = team_data.get("logo", "https://example.com/default-team-logo.png")
                    country_name = country_data.get("name", None)

                    # Validación del país
                    if country_name:
                        country_result = await country_postgres.get_country_by_name(db, country_name)
                        if not country_result:
                            logger.warning(f"Country '{country_name}' not found in DB. Setting country_name to None.")
                            country_name = None

                    if not team_id or not team_name:
                        logger.warning(f"Skipping team with invalid data: {item}")
                        failed_count += 1
                        failed_teams.append(item)
                        continue

                    logger.info(f"Adding or updating team: {team_name} (ID: {team_id})")
                    await team_postgres.add_or_update_team(db, team_id, team_name, country_name, team_logo)
                    added_count += 1
                except Exception as ex:
                    failed_count += 1
                    failed_teams.append(item)
                    logger.exception(f"Error adding team {team_name}: {ex}")

        logger.info(
            f"Teams process completed: added={added_count}, failed={failed_count}"
        )

        if failed_teams:
            logger.warning(f"Failed teams: {failed_teams}")

        return JSONResponse(
            content={
                "status": "success",
                "teams_added": added_count,
                "teams_failed": failed_count,
                "failed_teams": failed_teams,
            },
            status_code=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error fetching teams")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error fetching teams")
