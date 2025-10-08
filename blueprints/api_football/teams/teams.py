import logging
import requests
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from core.api_connection.connection import apiFutbolServicio
from services.teams.teams_postgres import TeamPostgres
from services.country.country_postgres import CountryPostgres
from services.leagues.leagues_postgres import LeaguePostgres
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger("teams_AF_logger")
logger.setLevel(logging.INFO)

api_endpoint = os.getenv("API_ENDPOINT")

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

teams_router_AF = APIRouter()


@teams_router_AF.get("/api/teams")
async def get_teams(db: AsyncSession = Depends(get_db)):
    apiFutbol = apiFutbolServicio(endpoint=api_endpoint)
    team_postgres = TeamPostgres()
    league_postgres = LeaguePostgres()
    country_postgres = CountryPostgres()

    logger.info("Fetching teams from external API...")

    try:
        leagues = await league_postgres.get_all_leagues(db)
        if not leagues:
            raise HTTPException(status_code=404, detail="No leagues found in database")

        logger.info(f"Retrieved {len(leagues)} leagues from the database.")

        added_count = 0
        failed_count = 0
        failed_teams = []

        for league in leagues:
            try:
                logger.info(f"Fetching teams for league: {league.name}")

                respuesta = None
                season = league.season
                try:
                    respuesta = apiFutbol.Equipos(liga=league.id, season=season)
                    if respuesta:
                        logger.info(
                            f"Received {len(respuesta)} teams for {league.name} season {season}."
                        )
                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout fetching teams for {league.name} season {season}. Retrying next season...")
                except requests.exceptions.ConnectionError:
                    logger.warning(f"Connection error fetching {league.name} season {season}. Skipping league.")
                    break
                except requests.HTTPError as e:
                    logger.warning(f"HTTP error fetching {league.name} season {season}: {e}")
                except Exception as e:
                    logger.warning(f"Unexpected error fetching {league.name} season {season}: {e}")

                if not respuesta:
                    logger.warning(f"No teams found for {league.name} (seasons 2025/2026). Skipping.")
                    continue

                for item in respuesta:
                    try:
                        team_data = item.get("team", {})

                        team_id = team_data.get("id")
                        team_name = team_data.get("name", "Unknown")
                        team_logo = team_data.get("logo", "https://example.com/default-team-logo.png")
                        country_name = team_data.get("country", "Uknown")

                        if not team_id or not team_name:
                            logger.warning(f"Invalid team data: {item}")
                            failed_count += 1
                            failed_teams.append(item)
                            continue

                        if country_name:
                            country_result = await country_postgres.get_country_by_name(db, country_name)
                            if not country_result:
                                logger.warning(f"Country '{country_name}' not found. Setting to None.")
                                country_name = None

                        await team_postgres.add_or_update_team(db, team_id, team_name, country_name, team_logo)
                        logger.info(f"Added or updated team: {team_name} (ID: {team_id})")
                        added_count += 1

                    except Exception as ex:
                        failed_count += 1
                        failed_teams.append(item)
                        logger.exception(f"Error adding team {team_name}: {ex}")

            except Exception as league_error:
                logger.exception(f"Unexpected error processing league {league.name}: {league_error}")
                continue

        logger.info(f"Teams process completed: added={added_count}, failed={failed_count}")

        return JSONResponse(
            content={
                "status": "success",
                "teams_added": added_count,
                "teams_failed": failed_count,
                "failed_teams": failed_teams,
            },
            status_code=status.HTTP_201_CREATED,
        )

    except HTTPException as e:
        raise e

    except requests.exceptions.RequestException as e:
        logger.exception(f"External API request failed: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch data from external API")

    except Exception as e:
        logger.exception(f"Unexpected server error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching teams")
