import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.future import select

# ============================================================
# Database setup — now uses in-memory SQLite
# ============================================================

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
Base = declarative_base()

# ============================================================
# Models
# ============================================================

class Country(Base):
    __tablename__ = "countries"
    name = Column(String(100), primary_key=True)
    code = Column(String(10))
    flag = Column(String(200))

    def to_json(self):
        return {"name": self.name, "code": self.code, "flag": self.flag}


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country_name = Column(String, ForeignKey("countries.name"), nullable=False)
    logo = Column(String(500), nullable=True)

    country = relationship("Country")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "country_name": self.country_name,
            "logo": self.logo,
        }

# ============================================================
# Services
# ============================================================

class CountryPostgres:
    async def get_country_by_name(self, db, name):
        result = await db.execute(select(Country).where(Country.name == name))
        return result.scalar_one_or_none()


class TeamPostgres:
    async def add_team(self, db: AsyncSession, id: int, name: str, country_name: str, logo: str = None):
        team = Team(id=id, name=name, country_name=country_name, logo=logo)
        db.add(team)
        await db.commit()
        await db.refresh(team)
        return team

    async def add_or_update_team(self, db: AsyncSession, id: int, name: str, country_name: str, logo: str = None):
        result = await db.execute(select(Team).where(Team.id == id))
        existing_team = result.scalars().first()
        if existing_team:
            existing_team.name = name
            existing_team.country_name = country_name
            existing_team.logo = logo
            await db.commit()
            return existing_team
        return await self.add_team(db, id, name, country_name, logo)

    async def add_or_skip_team(self, db: AsyncSession, id: int, name: str, country_name: str, logo: str = None):
        result = await db.execute(select(Team).where(Team.id == id))
        existing_team = result.scalars().first()
        if existing_team:
            return existing_team
        return await self.add_team(db, id, name, country_name, logo)

    async def get_team_by_id(self, db: AsyncSession, id: int):
        result = await db.execute(select(Team).where(Team.id == id))
        return result.scalar_one_or_none()

# ============================================================
# Tests
# ============================================================

@pytest.mark.asyncio
async def test_team_postgres_crud():
    """Ensure TeamPostgres works correctly using in-memory DB."""
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    service = TeamPostgres()

    async with async_session() as db:
        # Add dummy country first
        country = Country(name="Testland", code="TL", flag="🇹🇱")
        db.add(country)
        await db.commit()
        await db.refresh(country)

        # Add new team
        t1 = await service.add_team(db, id=1, name="FC Test", country_name="Testland", logo="logo.png")
        assert t1.id == 1
        assert t1.name == "FC Test"
        assert t1.country_name == "Testland"

        # Add or skip should return same
        t2 = await service.add_or_skip_team(db, id=1, name="Changed Name", country_name="Testland")
        assert t2.id == t1.id
        assert t2.name == "FC Test"  # Not updated because skipped

        # Add or update should update
        t3 = await service.add_or_update_team(db, id=1, name="FC Updated", country_name="Testland", logo="newlogo.png")
        assert t3.id == 1
        assert t3.name == "FC Updated"
        assert t3.logo == "newlogo.png"

        # Get team by ID
        t4 = await service.get_team_by_id(db, 1)
        assert t4.id == 1
        assert t4.name == "FC Updated"

    await engine.dispose()
