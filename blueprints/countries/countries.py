# blueprints/countries/countries.py
import logging
import requests
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db  
from core.api_connection.connection import apiFutbolServicio
from services.country.country_postgres import CountryPostgres

logger = logging.getLogger("countries_logger")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

countries_router = APIRouter()

@countries_router.get("/api/countries")
async def get_countries(db: AsyncSession = Depends(get_db)):
    apiFutbol = apiFutbolServicio(endpoint="https://api-football-v1.p.rapidapi.com/v3")
    country_postgres = CountryPostgres()

    logger.info("Fetching countries from external API...")

    try:
        respuesta = apiFutbol.Paises()
        logger.info(f"Received {len(respuesta)} countries from API.")
    except requests.HTTPError as e:
        logger.exception(f"HTTP error fetching countries: {e}")
        raise HTTPException(status_code=500, detail="Error fetching countries from API")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error fetching countries")

    added_count = 0
    failed_count = 0

    for country in respuesta:
        try:
            name = country.get("name")
            code = country.get("code")
            flag = country.get("flag")

            logger.info(f"Adding country: {name} ({code})")
            await country_postgres.add_country(db, name, code, flag)
            added_count += 1
        except Exception as ex:
            failed_count += 1
            logger.exception(f"Error adding country {name}: {ex}")

    logger.info(
        f"Countries process completed: added={added_count}, failed={failed_count}"
    )

    return JSONResponse(
        content={
            "status": "success",
            "countries_added": added_count,
            "countries_failed": failed_count,
        },
        status_code=status.HTTP_202_ACCEPTED,
    )
