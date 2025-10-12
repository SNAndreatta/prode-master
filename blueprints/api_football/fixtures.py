import logging
import requests
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from core.api_connection import apiFutbolServicio
from services.fixture_postgres import FixturePostgres
from services.leagues_postgres import LeaguePostgres
from dotenv import load_dotenv
import os
from models.fixture_status import string_to_enum
from datetime import datetime, timezone


load_dotenv()

logger = logging.getLogger("fixtures_AF_logger")
logger.setLevel(logging.INFO)

api_endpoint = os.getenv("API_ENDPOINT")

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

fixtures_router_AF = APIRouter()


@fixtures_router_AF.get("/api/fixtures")
async def get_fixtures(db: AsyncSession = Depends(get_db)):
    apiFutbol = apiFutbolServicio(endpoint=api_endpoint)
    league_postgres = LeaguePostgres()
    fixture_postgres = FixturePostgres()

    logger.info("Fetching fixtures from external API...")

    try:
        leagues = await league_postgres.get_all_leagues(db)

        if not leagues:
            raise HTTPException(status_code=404, detail="No leagues found in database")

        logger.info(f"Retrieved {len(leagues)} leagues from the database.")

        added_count = 0
        failed_count = 0
        failed_fixtures = []

        for league in leagues:
            try:
                logger.info(f"Fetching fixtures for league: {league.name}")

                respuesta = None
                season = league.season

                try:
                    respuesta = apiFutbol.fixtures_from_api(liga=league.id, season=season)
                    if respuesta:
                        logger.info(
                            f"Received {len(respuesta)} fixtures for {league.name} season {season}."
                        )
                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout fetching fixtures for {league.name}. Retrying next league...")
                    continue
                except requests.exceptions.ConnectionError:
                    logger.warning(f"Connection error fetching {league.name}. Skipping league.")
                    continue
                except requests.HTTPError as e:
                    logger.warning(f"HTTP error fetching {league.name}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Unexpected error fetching {league.name}: {e}")
                    continue

                if not respuesta:
                    logger.warning(f"No fixtures found for {league.name}. Skipping.")
                    continue

                for item in respuesta:
                    try:
                        fixture_data = item.get("fixture", {})
                        league_data = item.get("league", {})
                        teams_data = item.get("teams", {})
                        goals_data = item.get("goals", {})
                        score_data = item.get("score", {})

                        fixture_id = fixture_data.get("id")

                        round = league_data.get("round")

                        # Pasar a DateTime
                        # Ejemplo: 2025-01-22T21:10:00-03:00
                        date_str = fixture_data.get("date")
                        date = None

                        if date_str:
                            try:
                                # Convierte "2025-01-22T21:10:00-03:00" a datetime con zona horaria
                                local_dt = datetime.fromisoformat(date_str)
                                # Lo pasás a UTC (opcional, pero recomendable)
                                date = local_dt.astimezone(timezone.utc)
                            except Exception as e:
                                logger.warning(f"Invalid date format: {date_str} - {e}")
                                date = None

                        status_data = fixture_data.get("status", {})
                        status_short = status_data.get("short")

                        home_team = teams_data.get("home", {})
                        away_team = teams_data.get("away", {})

                        home_id = home_team.get("id")
                        away_id = away_team.get("id")

                        home_score = goals_data.get("home")
                        away_score = goals_data.get("away")

                        home_pen_score = (
                            score_data.get("penalty", {}).get("home")
                            if score_data.get("penalty")
                            else None
                        )
                        away_pen_score = (
                            score_data.get("penalty", {}).get("away")
                            if score_data.get("penalty")
                            else None
                        )

                        if not all([fixture_id, league_data.get("id"), home_id, away_id]):
                            logger.warning(f"Invalid fixture data: {item}")
                            failed_count += 1
                            failed_fixtures.append(item)
                            continue

                        status_enum = string_to_enum(status_short)

                        await fixture_postgres.add_or_update_fixture(
                            db=db,
                            id=fixture_id,
                            league_id=league_data.get("id"),
                            home_id=home_id,
                            away_id=away_id,
                            date=date,
                            home_team_score=home_score,
                            away_team_score=away_score,
                            home_pens_score=home_pen_score,
                            away_pens_score=away_pen_score,
                            status=status_enum,
                            round=round
                        )

                        added_count += 1
                        logger.info(f"Added/updated fixture {fixture_id} ({league_data.get('name')})")

                    except Exception as ex:
                        failed_count += 1
                        failed_fixtures.append(item)
                        logger.exception(f"Error adding fixture {fixture_data.get('id')}: {ex}")

            except Exception as league_error:
                logger.exception(f"Unexpected error processing league {league.name}: {league_error}")
                continue

        logger.info(f"Fixtures process completed: added={added_count}, failed={failed_count}")

        return JSONResponse(
            content={
                "status": "success",
                "fixtures_added": added_count,
                "fixtures_failed": failed_count,
                "failed_fixtures": failed_fixtures,
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
        raise HTTPException(status_code=500, detail="Internal server error while fetching fixtures")
