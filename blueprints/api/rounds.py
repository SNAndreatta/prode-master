# blueprints/fixtures/fixtures.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.fixture_valkey import FixtureValkey
from services.fixture_postgres import FixturePostgres
from services.leagues_postgres import LeaguePostgres
from services.round_postgres import RoundPostgres
from models.fixtures.fixture import Fixture
from dotenv import load_dotenv
import os
import valkey


rounds_router = APIRouter()

logger = logging.getLogger("fixtures_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


@rounds_router.get("/fixtures")
async def get_fixtures_by_league_and_round(
    league_id: int = Query(..., description="ID de la liga"),
    round_name: str = Query(..., description="Nombre de la ronda"),
    db: AsyncSession = Depends(get_db)
):
    """
    Devuelve todos los fixtures de una liga y ronda específica.
    Ejemplo: /fixtures?league_id=39&round_name=Regular Season - 10
    """
    try:
        fixture_valkey = FixtureValkey(await get_valkey_client())
        league_postgres = LeaguePostgres()
        round_postgres = RoundPostgres()

        json_fixtures = await fixture_valkey.get_fixtures_by_league_and_round_and_teams(league_id, round_name, db)
        league = await league_postgres.get_league_by_id(db, league_id)
        round = await round_postgres.get_round_by_name(db, round_name)

        logger.info(f"Process completed: obtained={len(json_fixtures)} fixtures")

        return JSONResponse(
            content={
                "status": "success",
                "league": league.to_json(),
                "round": round.to_json(),
                "fixtures": json_fixtures
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error fetching fixtures")


@rounds_router.get("/rounds/by-league")
async def get_rounds_by_league(
    league_id: int = Query(..., description="ID de la liga"),
    season: int = Query(None, description="Temporada (opcional)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Devuelve todas las rondas de una liga específica.
    Opcionalmente se puede filtrar por temporada.
    Ejemplo: /rounds/by-league?league_id=39&season=2023
    """
    try:
        round_postgres = RoundPostgres()
        league_postgres = LeaguePostgres()

        # Obtener la liga para validar que existe
        league = await league_postgres.get_league_by_id(db, league_id)
        if not league:
            raise HTTPException(status_code=404, detail=f"League with ID {league_id} not found")

        # Obtener las rondas
        rounds = await round_postgres.get_rounds_by_league(db, league_id, season)
        json_rounds = round_postgres.rounds_to_json(rounds)

        logger.info(f"Found {len(rounds)} rounds for league {league_id}")

        return JSONResponse(
            content={
                "status": "success",
                "league": league.to_json(),
                "rounds": json_rounds,
                "count": len(rounds)
            },
            status_code=status.HTTP_200_OK
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error fetching rounds")
