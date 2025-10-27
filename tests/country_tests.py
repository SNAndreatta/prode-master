import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from models.countries import Base, Country
from services.country_service import CountryPostgres


# --- FIXTURE DE LA BASE DE DATOS EN MEMORIA ---

@pytest.fixture(scope="session")
def event_loop():
    """Permite que pytest-asyncio use un solo event loop por sesión."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_engine():
    """Crea un motor SQLite en memoria para los tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def session(async_engine):
    """Crea una nueva sesión para cada test."""
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()  # Limpia la DB después de cada test


@pytest.fixture(scope="function")
def country_service():
    """Instancia del servicio de países."""
    return CountryPostgres()


# --- TESTS ---

@pytest.mark.asyncio
async def test_add_country(session: AsyncSession, country_service: CountryPostgres):
    country = await country_service.add_country(session, name="France", code="FR", flag="https://example.com/fr-flag.png")

    assert country.name == "France"
    assert country.code == "FR"
    assert country.flag == "https://example.com/fr-flag.png"

    result = await session.execute(text("SELECT * FROM countries WHERE code = 'FR'"))
    db_country = result.fetchone()
    assert db_country is not None
    assert db_country.name == "France"


@pytest.mark.asyncio
async def test_add_or_update_country_add(session: AsyncSession, country_service: CountryPostgres):
    country = await country_service.add_or_update_country(session, name="Germany", code="DE", flag="https://example.com/de-flag.png")

    assert country.name == "Germany"
    assert country.code == "DE"
    
    result = await session.execute(text("SELECT * FROM countries WHERE code = 'DE'"))
    db_country = result.fetchone()
    assert db_country is not None
    assert db_country.name == "Germany"


@pytest.mark.asyncio
async def test_add_or_update_country_update(session: AsyncSession, country_service: CountryPostgres):
    await country_service.add_country(session, name="Italy", code="IT", flag="https://example.com/it-flag.png")

    updated_country = await country_service.add_or_update_country(session, name="Italy", code="IT", flag="https://example.com/new-it-flag.png")
    
    assert updated_country.name == "Italy"
    assert updated_country.flag == "https://example.com/new-it-flag.png"

    result = await session.execute(text("SELECT * FROM countries WHERE code = 'IT'"))
    db_country = result.fetchone()
    assert db_country is not None
    assert db_country.flag == "https://example.com/new-it-flag.png"


@pytest.mark.asyncio
async def test_add_or_skip_country(session: AsyncSession, country_service: CountryPostgres):
    country = await country_service.add_or_skip_country(session, name="Spain", code="ES", flag="https://example.com/es-flag.png")
    
    assert country.name == "Spain"

    existing_country = await country_service.add_or_skip_country(session, name="Spain", code="ES", flag="https://example.com/new-es-flag.png")
    assert existing_country.id == country.id


@pytest.mark.asyncio
async def test_get_all_countries(session: AsyncSession, country_service: CountryPostgres):
    await country_service.add_country(session, name="France", code="FR", flag="https://example.com/fr-flag.png")
    await country_service.add_country(session, name="Germany", code="DE", flag="https://example.com/de-flag.png")

    countries = await country_service.get_all_countries(session)
    assert len(countries) == 2
    assert any(country.name == "France" for country in countries)
    assert any(country.name == "Germany" for country in countries)


@pytest.mark.asyncio
async def test_get_country_by_name(session: AsyncSession, country_service: CountryPostgres):
    country = await country_service.add_country(session, name="Japan", code="JP", flag="https://example.com/jp-flag.png")
    
    fetched_country = await country_service.get_country_by_name(session, name="Japan")
    assert fetched_country is not None
    assert fetched_country.name == "Japan"
    assert fetched_country.code == "JP"
