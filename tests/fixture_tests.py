import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.fixtures.fixture import Fixture
from models.fixtures.fixture_status import FixtureStatus
from services.fixture_postgres import FixturePostgres
from database import Base


# ============================================================
# Pytest Fixtures
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """Usa un solo event loop por sesión (requerido por pytest-asyncio)."""
    import asyncio
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_engine():
    """Crea un motor SQLite en memoria para todos los tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def session(async_engine):
    """Crea una sesión nueva para cada test y limpia al finalizar."""
    async_session = sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def fixture_service():
    """Instancia del servicio FixturePostgres."""
    return FixturePostgres()


# ============================================================
# Tests
# ============================================================

@pytest.mark.asyncio
async def test_add_new_fixture(session, fixture_service: FixturePostgres):
    fixture_id = 1
    date = datetime.utcnow() + timedelta(days=1)

    await fixture_service.add_or_update_fixture(
        db=session,
        id=fixture_id,
        league_id=10,
        home_id=100,
        away_id=200,
        date=date,
        home_team_score=0,
        away_team_score=0,
        home_pens_score=0,
        away_pens_score=0,
        status=FixtureStatus.NS,
        round="Round 1",
    )

    result = await fixture_service.get_fixture_by_id(session, fixture_id)
    assert result is not None
    assert result.id == fixture_id
    assert result.status == FixtureStatus.NS


@pytest.mark.asyncio
async def test_update_existing_fixture(session, fixture_service: FixturePostgres):
    fixture_id = 2
    date = datetime.utcnow()

    # Agrega fixture
    await fixture_service.add_or_update_fixture(
        db=session,
        id=fixture_id,
        league_id=20,
        home_id=101,
        away_id=202,
        date=date,
        home_team_score=1,
        away_team_score=0,
        home_pens_score=0,
        away_pens_score=0,
        status=FixtureStatus.NS,
        round="Round 2",
    )

    # Actualiza fixture
    await fixture_service.add_or_update_fixture(
        db=session,
        id=fixture_id,
        league_id=20,
        home_id=101,
        away_id=202,
        date=date,
        home_team_score=2,
        away_team_score=2,
        home_pens_score=0,
        away_pens_score=0,
        status=FixtureStatus.FT,
        round="Round 2",
    )

    updated = await fixture_service.get_fixture_by_id(session, fixture_id)
    assert updated.home_team_score == 2
    assert updated.status == FixtureStatus.FT


@pytest.mark.asyncio
async def test_get_all_data(session, fixture_service: FixturePostgres):
    # Agrega múltiples fixtures
    for i in range(3):
        await fixture_service.add_or_update_fixture(
            db=session,
            id=i + 1,
            league_id=1,
            home_id=100 + i,
            away_id=200 + i,
            date=datetime.utcnow(),
            home_team_score=0,
            away_team_score=0,
            home_pens_score=0,
            away_pens_score=0,
            status=FixtureStatus.NS,
            round="R1",
        )

    results = await fixture_service.get_all_data(session)
    assert len(results) == 3


@pytest.mark.asyncio
async def test_get_fixtures_by_league_and_round(session, fixture_service: FixturePostgres):
    await fixture_service.add_or_update_fixture(
        db=session,
        id=10,
        league_id=55,
        home_id=101,
        away_id=202,
        date=datetime.utcnow(),
        home_team_score=1,
        away_team_score=0,
        home_pens_score=0,
        away_pens_score=0,
        status=FixtureStatus.NS,
        round="Final",
    )

    results = await fixture_service.get_fixtures_by_league_and_round(
        session, league_id=55, round_name="Final"
    )
    assert len(results) == 1
    assert results[0].league_id == 55
    assert results[0].round == "Final"


def test_fixture_lock_logic(fixture_service: FixturePostgres):
    """Prueba la lógica de bloqueo de fixture y si empezó por fecha."""
    now = datetime.utcnow()

    # Case 1: Finalizado -> bloqueado
    f1 = Fixture(
        id=1, league_id=1, home_id=1, away_id=2,
        date=now, home_team_score=1, away_team_score=0,
        home_pens_score=0, away_pens_score=0,
        status=FixtureStatus.FT, round="R1"
    )
    assert fixture_service._is_fixture_locked(f1)

    # Case 2: Futuro -> no bloqueado
    f2 = Fixture(
        id=2, league_id=1, home_id=1, away_id=2,
        date=now + timedelta(days=1),
        home_team_score=0, away_team_score=0,
        home_pens_score=0, away_pens_score=0,
        status=FixtureStatus.NS, round="R1"
    )
    assert not fixture_service._is_fixture_locked(f2)

    # Case 3: Pasado -> bloqueado
    f3 = Fixture(
        id=3, league_id=1, home_id=1, away_id=2,
        date=now - timedelta(hours=1),
        home_team_score=0, away_team_score=0,
        home_pens_score=0, away_pens_score=0,
        status=FixtureStatus.NS, round="R1"
    )
    assert fixture_service._is_fixture_locked(f3)

    # Case 4: is_fixture_started_by_date
    assert fixture_service.is_fixture_started_by_date(f3)
    assert not fixture_service.is_fixture_started_by_date(f2)
