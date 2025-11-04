import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer

# === In-memory database setup ===
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
Base = declarative_base()

# Example table for quick persistence check
class DummyModel(Base):
    __tablename__ = "dummy"
    id = Column(Integer, primary_key=True)

# === Import your real service ===
from services.prediction_points import PredictionPointsService


@pytest.mark.asyncio
async def test_prediction_points_service_scoring():
    """Ensure PredictionPointsService returns correct scores."""
    service = PredictionPointsService()

    # exact match
    points, reason = service.score_prediction(2, 1, 2, 1)
    assert points == 3 and reason == "exact"

    # correct winner (same winner, different score)
    points, reason = service.score_prediction(3, 1, 2, 0)
    assert points == 1 and reason == "winner"

    # draw case
    points, reason = service.score_prediction(2, 2, 1, 1)
    assert points == 1 and reason == "winner"

    # wrong result
    points, reason = service.score_prediction(0, 3, 2, 1)
    assert points == 0 and reason == "wrong"


@pytest.mark.asyncio
async def test_database_connection_and_commit():
    """Simple async test to ensure in-memory DB connection and commit works."""
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        dummy = DummyModel()
        session.add(dummy)
        await session.commit()

        result = await session.get(DummyModel, dummy.id)
        assert result is not None

    await engine.dispose()
