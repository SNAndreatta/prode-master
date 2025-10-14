import logging
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from core.api_connection import apiFutbolServicio
from services.round_postgres import RoundPostgres
from services.leagues_postgres import LeaguePostgres

async def get_rounds(api_endpoint: str, db: AsyncSession = Depends(get_db)):
    logger = logging.getLogger("rounds_AF_logger")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    apiFutbol = apiFutbolServicio(endpoint=api_endpoint)
    round_postgres = RoundPostgres()
    league_postgres = LeaguePostgres()

    logger.info("Fetching rounds from external API...")

    try:
        leagues = await league_postgres.get_all_leagues(db)

        logger.info(f"Found {len(leagues)} leagues in database.")

        added_count = 0
        failed_count = 0
        failed_rounds = []

        for league in leagues:
            if league.id in [131, 132, 134, 906, 1067]:
                continue

            league_id = league.id
            season_year = league.season

            logger.info(f"Fetching rounds for league {league.name} (ID: {league_id}, season: {season_year})")

            try:
                respuesta = apiFutbol.rounds_from_api(liga=league_id, season=season_year)

                if not respuesta:
                    logger.warning(f"No rounds found for league {league.name} ({league_id}) season {season_year}")
                    continue

                for round_name in respuesta:
                    try:
                        await round_postgres.add_or_skip_round(
                            db=db,
                            name=round_name,
                            league_id=league_id,
                            season=season_year
                        )
                        added_count += 1
                    except Exception as ex:
                        failed_count += 1
                        failed_rounds.append({
                            "league_id": league_id,
                            "season": season_year,
                            "round_name": round_name,
                            "error": str(ex)
                        })
                        logger.exception(f"Error adding round {round_name} for league {league.name}: {ex}")

            except Exception as e:
                logger.exception(f"Unexpected error fetching rounds for league {league_id}: {e}")
                continue

        logger.info(f"Rounds process completed: added={added_count}, failed={failed_count}")
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise e
