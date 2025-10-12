# blueprints/countries/countries.py
import logging
from fastapi import HTTPException, status, Depends, APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db  
from services.country_postgres import CountryPostgres
from services.leagues_postgres import LeaguePostgres
from dotenv import load_dotenv
import os

countries_router = APIRouter()

load_dotenv()

logger = logging.getLogger("countries_logger")
logger.setLevel(logging.INFO)

api_endpoint = os.getenv("API_ENDPOINT")

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

@countries_router.get("/countries")
async def get_countries(db: AsyncSession = Depends(get_db)):
    try:
        country_postgres = CountryPostgres()

        logger.info("Fetching countries from database...")

        countries = await country_postgres.get_all_countries(db)

        logger.info(
            f"Countries process completed: obtained={len(countries)}"
        )

        json_countries = country_postgres.countries_to_json(countries)

        return JSONResponse(
            content={
                "status": "success",
                "countries": json_countries
            },
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error fetching database countries")
    
@countries_router.get("/countries_with_league")
async def get_countries_with_league(db: AsyncSession = Depends(get_db)):
    try:
        league_postgres = LeaguePostgres()
        country_postgres = CountryPostgres()

        logger.info("Fetching countries with leagues from database...")

        countries = await league_postgres.get_all_countries_with_league(db)

        logger.info(
            f"Countries process completed: obtained={len(countries)}"
        )

        json_countries = country_postgres.countries_to_json(countries)

        return JSONResponse(
            content={
                "status": "success",
                "countries": json_countries
                },
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error fetching database countries")