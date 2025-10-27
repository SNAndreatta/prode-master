import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey
from services.tournament_services import TournamentPostgres, TournamentParticipationPostgres

# === Base de datos en memoria ===
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
Base = declarative_base()

# === Modelos mínimos ===
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)


class League(Base):
    __tablename__ = "leagues"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)


class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"))
    league_id = Column(Integer, ForeignKey("leagues.id"))

    creator = relationship("User")
    league = relationship("League")


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    tournament = relationship("Tournament")
    user = relationship("User")


# === TEST ===
@pytest.mark.asyncio
async def test_tournament_participation_crud():
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Crear esquema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    tournament_service = TournamentPostgres()
    participation_service = TournamentParticipationPostgres()

    async with async_session() as db:
        # Crear usuario y liga dummy
        user = User(username="testuser")
        league = League(name="Premier League")
        db.add_all([user, league])
        await db.commit()
        await db.refresh(user)
        await db.refresh(league)

        # --- CRUD de torneos ---
        tournament = await tournament_service.create_tournament(
            db, name="Test Tournament", creator_id=user.id, league_id=league.id
        )
        assert tournament.id is not None
        assert tournament.name == "Test Tournament"

        fetched = await tournament_service.get_tournament_by_id(db, tournament.id)
        assert fetched.id == tournament.id

        updated = await tournament_service.update_tournament(
            db, tournament.id, creator_id=user.id, name="Updated Tournament"
        )
        assert updated.name == "Updated Tournament"

        creator_tournaments = await tournament_service.get_tournaments_by_creator(db, user.id)
        assert len(creator_tournaments) == 1

        league_tournaments = await tournament_service.get_tournaments_by_league(db, league.id)
        assert len(league_tournaments) == 1

        # --- Participación en torneos ---
        participation = await participation_service.join_tournament(db, tournament.id, user.id)
        assert participation.tournament_id == tournament.id
        assert participation.user_id == user.id

        # Intentar unirse dos veces debe fallar
        with pytest.raises(ValueError):
            await participation_service.join_tournament(db, tournament.id, user.id)

        is_part = await participation_service.is_participant(db, tournament.id, user.id)
        assert is_part is True

        participants = await participation_service.get_tournament_participants(db, tournament.id)
        assert len(participants) == 1
        assert participants[0].user.id == user.id

        left = await participation_service.leave_tournament(db, tournament.id, user.id)
        assert left is True

        left_again = await participation_service.leave_tournament(db, tournament.id, user.id)
        assert left_again is False

        deleted = await tournament_service.delete_tournament(db, tournament.id, creator_id=user.id)
        assert deleted is True

    await engine.dispose()
