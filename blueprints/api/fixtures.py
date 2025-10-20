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

async def get_valkey_client():
    """Create and return Valkey client using valkey library"""
    load_dotenv()
    valkey_uri = os.getenv("VALKEY_URI")
    if not valkey_uri:
        raise ValueError("VALKEY_URI not found in environment variables")
    
    return valkey.from_url(valkey_uri)

fixtures_router = APIRouter()

logger = logging.getLogger("fixtures_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


@fixtures_router.get("/fixtures")
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
