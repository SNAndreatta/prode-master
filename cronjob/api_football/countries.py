import logging
from core.api_connection import apiFutbolServicio
from services.country_postgres import CountryPostgres
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from database import get_db

async def get_countries(api_endpoint: str, db: AsyncSession):
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
        
    logger = logging.getLogger("countries_AF_logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    apiFutbol = apiFutbolServicio(endpoint=api_endpoint)
    country_postgres = CountryPostgres()

    logger.info("Fetching countries from external API...")

    try:
        respuesta = apiFutbol.countries_from_api()
        logger.info(f"Received {len(respuesta)} countries from API.")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise e
    
    added_count = 0
    failed_count = 0
    failed_countries = []

    for country in respuesta:
        try:
            name = country.get("name", "Unknown")
            code = country.get("code", name[:3].upper())
            flag = country.get("flag", "https://example.com/default-flag.png")

            logger.info(f"Adding or updating country: {name} ({code})")
            await country_postgres.add_or_update_country(db, name, code, flag)
            added_count += 1
        except Exception as ex:
            failed_count += 1
            failed_countries.append(country) 
            logger.exception(f"Error adding country {name}: {ex}")

    logger.info(f"Countries process completed: added={added_count}, failed={failed_count}")

    if failed_countries:
        logger.warning(f"Failed countries: {failed_countries}")
