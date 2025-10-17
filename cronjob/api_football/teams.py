import logging
import requests
from fastapi import Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from core.api_connection import apiFutbolServicio
from services.teams_postgres import TeamPostgres
from services.country_postgres import CountryPostgres
from services.leagues_postgres import LeaguePostgres

async def get_teams(api_endpoint: str, db: AsyncSession = Depends(get_db)):
    logger = logging.getLogger("teams_AF_logger")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    apiFutbol = apiFutbolServicio(endpoint=api_endpoint)
    team_postgres = TeamPostgres()
    league_postgres = LeaguePostgres()
    country_postgres = CountryPostgres()

    logger.info("Fetching teams from external API...")

    try:
        leagues = await league_postgres.get_all_leagues(db)
        if not leagues:
            raise Exception("No leagues found in database")

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
                    respuesta = apiFutbol.teams_from_api(liga=league.id, season=season)
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

    except Exception as e:
        logger.exception(f"Unexpected server error: {e}")
        raise e