import logging
import requests
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from core.api_connection import apiFutbolServicio
from services.leagues_postgres import LeaguePostgres
from services.country_postgres import CountryPostgres
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger("leagues_AF_logger")
logger.setLevel(logging.INFO)

api_endpoint = os.getenv("API_ENDPOINT")

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

leagues_router_AF = APIRouter()


@leagues_router_AF.get("/api/leagues")
async def get_leagues(db: AsyncSession = Depends(get_db)):
    apiFutbol = apiFutbolServicio(endpoint=api_endpoint)
    league_postgres = LeaguePostgres()
    country_postgres = CountryPostgres()

    logger.info("Fetching leagues from external API...")

    try:
        country_names = ["Argentina", "Brasil", "World", "Spain", "England", "Italy"]
        logger.info(f"Fetching countries by names: {country_names}")

        countries = []
        for name in country_names:
            result = await country_postgres.get_country_by_name(db, name)
            if result:
                countries.append(result)
            else:
                logger.warning(f"Country not found in the database: {name}")

        logger.info(f"Retrieved {len(countries)} countries from the database.")

        added_count = 0
        failed_count = 0
        failed_leagues = []

        leagues_ids = [2, 3, 11, 13, 15, 34, 39, 128, 129, 130, 131, 132, 134, 135, 140, 848, 906, 1067]

        for country in countries:
            country_name = country.name
            logger.info(f"Fetching leagues for country: {country_name}")

            try:
                respuesta = apiFutbol.leagues_from_api(pais=country_name)
                logger.info(f"Received {len(respuesta)} leagues for country: {country_name}.")
            except requests.HTTPError as e:
                logger.exception(f"HTTP error fetching leagues for {country_name}: {e}")
                continue
            except Exception as e:
                logger.exception(f"Unexpected error fetching leagues for {country_name}: {e}")
                continue

            for item in respuesta:
                try:
                    league_info = item.get("league", {})
                    country_info = item.get("country", {})
                    seasons = item.get("seasons", [])

                    league_id = league_info.get("id")
                    league_name = league_info.get("name", "Unknown League")
                    league_logo = league_info.get("logo", "https://example.com/default-league-logo.png")
                    country_name = country_info.get("name", "Unknown Country")

                    if not league_id or not league_name or not country_name:
                        logger.warning(f"Skipping league with invalid data: {item}")
                        failed_count += 1
                        failed_leagues.append(item)
                        continue

                    if league_id not in leagues_ids:
                        logger.info(
                            f"Skipping league ID {league_id} ({league_name}) — not in allowed list."
                        )
                        continue

                    valid_seasons = [
                        s for s in seasons if s.get("year") in {2025, 2026}
                    ]

                    if not valid_seasons:
                        logger.info(
                            f"Skipping league {league_name} (ID: {league_id}) — no valid seasons (2025 or 2026)."
                        )
                        continue

                    for season in valid_seasons:
                        season_year = season.get("year")

                        logger.info(
                            f"Adding or updating league: {league_name} (ID: {league_id}) for season {season_year}"
                        )

                        await league_postgres.add_or_update_league(
                            db,
                            league_id,
                            league_name,
                            country_name,
                            season_year,
                            league_logo
                        )

                        added_count += 1

                except Exception as ex:
                    failed_count += 1
                    failed_leagues.append(item)
                    logger.exception(f"Error adding league {league_name}: {ex}")

        logger.info(f"Leagues process completed: added={added_count}, failed={failed_count}")

        if failed_leagues:
            logger.warning(f"Failed leagues: {failed_leagues}")

        return JSONResponse(
            content={
                "status": "success",
                "leagues_added": added_count,
                "leagues_failed": failed_count,
                "failed_leagues": failed_leagues,
            },
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error fetching leagues")
