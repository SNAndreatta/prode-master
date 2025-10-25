# blueprints/countries/countries.py
import logging
from fastapi import HTTPException, status, Depends, APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db  
from services.leagues_postgres import LeaguePostgres
from services.country_postgres import CountryPostgres
from dotenv import load_dotenv
import os

load_dotenv()

leagues_router = APIRouter()

logger = logging.getLogger("leagues_logger")
logger.setLevel(logging.INFO)

api_endpoint = os.getenv("API_ENDPOINT")

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

@leagues_router.get("/leagues")
async def get_leagues(
    country_name: str | None = Query(None, description="Filtrar por nombre de país (opcional)"),
    db: AsyncSession = Depends(get_db)
):
    try:
        if not country_name:
            raise HTTPException(status_code=400, detail="Country name is required in querystring.")

        leagues_postgres = LeaguePostgres()
        country_postgres = CountryPostgres()

        logger.info(f"Fetching leagues from database for country: {country_name}...")
        leagues = await leagues_postgres.get_leagues_by_country(db, country_name)
        json_leagues = leagues_postgres.leagues_to_json(leagues)
        logger.info(f"Leagues process completed for {country_name}: obtained={len(leagues)}")
        
        country = await country_postgres.get_country_by_name(db, json_leagues[0]["country"])

        return JSONResponse(
        content={
            "status": "success",
            "country": country.to_json(),
            "leagues": json_leagues,
        },
        status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        else:
            logger.exception(f"Unexpected error fetching leagues: {e}")
            raise HTTPException(status_code=500, detail="Unexpected error fetching leagues")

@leagues_router.get("/leagues/{league_id}")
async def get_league_by_id(
    league_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a league by its ID.
    Returns detailed information about the league.
    """
    try:
        leagues_postgres = LeaguePostgres()

        logger.info(f"Fetching league from database for ID: {league_id}...")
        league = await leagues_postgres.get_league_by_id(db, league_id)

        if not league:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"League with ID {league_id} not found."
            )

        league_json = league.to_json() if hasattr(league, "to_json") else {
            "id": league.id,
            "name": league.name,
            "country": league.country,
            "season": league.season,
        }

        logger.info(f"League fetched successfully: {league_json.get('name', 'unknown')}")

        return JSONResponse(
            content={
                "status": "success",
                "league": league_json,
            },
            status_code=status.HTTP_200_OK,
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error fetching league by ID {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error fetching league")