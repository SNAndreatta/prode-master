# blueprints/countries/countries.py
import logging
from fastapi import HTTPException, status, Depends, APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db  
from services.leagues_postgres import LeaguePostgres
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
        leagues_postgres = LeaguePostgres()

        if country_name:
            logger.info(f"Fetching leagues from database for country: {country_name}...")
            leagues = await leagues_postgres.get_leagues_by_country(db, country_name)
            logger.info(f"Leagues process completed for {country_name}: obtained={len(leagues)}")
        else:
            logger.info("Fetching all leagues from database...")
            leagues = await leagues_postgres.get_all_leagues(db)
            logger.info(f"Leagues process completed: obtained={len(leagues)}")

        json_leagues = leagues_postgres.leagues_to_json(leagues)

        return JSONResponse(
            content={
                "status": "success",
                "country": country_name if country_name else "Unknown",
                "leagues": json_leagues,
            },
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.exception(f"Unexpected error fetching leagues: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error fetching leagues")
