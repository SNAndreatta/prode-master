import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.leagues import League
from services.leagues_postgres import LeaguePostgres
from models.countries import Country
from services.country_postgres import CountryPostgres

# ============================================================
# Setup (in-memory database)
# ============================================================

Base = League.__bases__[0]  # Usa el mismo Base compartido que los modelos
league_service = LeaguePostgres()
country_service = CountryPostgres()

# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_engine():
    """Crea el motor SQLite en memoria para todos los tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def session(async_engine):
    """Crea una nueva sesión limpia para cada test."""
    async_session = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
        await session.rollback()


# ============================================================
# Tests
# ============================================================

@pytest.mark.asyncio
async def test_add_league(session: AsyncSession):
    # Crear país asociado
    await country_service.add_country(session, name="England", code="ENG", flag="🏴")

    # Agregar liga
    league = await league_service.add_league(
        db=session,
        id=1,
        name="Premier League",
        country_name="England",
        season=2025,
        logo="premier_league_logo.png"
    )

    assert league.id == 1
    assert league.name == "Premier League"
    assert league.country_name == "England"
    assert league.season == 2025


@pytest.mark.asyncio
async def test_add_or_update_league(session: AsyncSession):
    await country_service.add_country(session, name="Spain", code="ESP", flag="🇪🇸")

    # Agregar
    l1 = await league_service.add_or_update_league(
        db=session,
        id=2,
        name="La Liga",
        country_name="Spain",
        season=2025,
        logo="laliga.png"
    )
    assert l1.name == "La Liga"

    # Actualizar
    l2 = await league_service.add_or_update_league(
        db=session,
        id=2,
        name="La Liga Santander",
        country_name="Spain",
        season=2025,
        logo="laliga_new.png"
    )
    assert l2.name == "La Liga Santander"
    assert l2.logo == "laliga_new.png"


@pytest.mark.asyncio
async def test_add_or_skip_league(session: AsyncSession):
    await country_service.add_country(session, name="Italy", code="ITA", flag="🇮🇹")

    # Primera vez
    l1 = await league_service.add_or_skip_league(
        db=session, id=3, name="Serie A", country_name="Italy", season=2025
    )

    # Intentar duplicar
    l2 = await league_service.add_or_skip_league(
        db=session, id=3, name="Serie A (Duplicate)", country_name="Italy", season=2025
    )

    assert l1.id == l2.id
    assert l2.name == "Serie A"  # no se actualiza


@pytest.mark.asyncio
async def test_get_all_and_by_country(session: AsyncSession):
    await country_service.add_country(session, name="France", code="FRA", flag="🇫🇷")

    await league_service.add_league(session, id=4, name="Ligue 1", country_name="France", season=2025)
    await league_service.add_league(session, id=5, name="Ligue 2", country_name="France", season=2025)

    all_leagues = await league_service.get_all_leagues(session)
    assert len(all_leagues) >= 2

    france_leagues = await league_service.get_leagues_by_country(session, "France")
    assert all(l.country_name == "France" for l in france_leagues)


@pytest.mark.asyncio
async def test_leagues_to_json(session: AsyncSession):
    await country_service.add_country(session, name="Germany", code="DEU", flag="🇩🇪")

    league = await league_service.add_league(
        session, id=6, name="Bundesliga", country_name="Germany", season=2025
    )

    leagues = [league]
    json_output = league_service.leagues_to_json(leagues)[0]

    assert json_output["name"] == "Bundesliga"
    assert json_output["country"] == "Germany"


@pytest.mark.asyncio
async def test_get_all_leagues_with_country_info(session: AsyncSession):
    await country_service.add_country(session, name="Portugal", code="PRT", flag="🇵🇹")

    await league_service.add_league(
        session, id=7, name="Primeira Liga", country_name="Portugal", season=2025
    )

    enriched = await league_service.get_all_leagues_with_country_info(session)
    assert isinstance(enriched, list)
    assert enriched[0]["country"]["code"] == "PRT"


@pytest.mark.asyncio
async def test_get_all_countries_with_league(session: AsyncSession):
    await country_service.add_country(session, name="Brazil", code="BRA", flag="🇧🇷")

    await league_service.add_league(
        session, id=8, name="Brasileirão", country_name="Brazil", season=2025
    )

    countries = await league_service.get_all_countries_with_league(session)
    assert any(c.name == "Brazil" for c in countries)
