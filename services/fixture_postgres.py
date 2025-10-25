from models.fixtures.fixture import Fixture
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models.fixtures.fixture_status import FixtureStatus
from services.teams_postgres import TeamPostgres
from datetime import datetime
from typing import Optional, Any, cast

class FixturePostgres:
    async def add_or_update_fixture(
        self,
        db: AsyncSession,
        id: int,
        league_id: int,
        home_id: int,
        away_id: int,
        date: Optional[datetime],
        home_team_score: int,
        away_team_score: int,
        home_pens_score: int,
        away_pens_score: int,
        status: FixtureStatus,
        round: str
    ):
        try:
            existing_fixture = await db.execute(select(Fixture).where(cast(Any, Fixture.id == id)))
            existing_fixture = existing_fixture.scalar_one_or_none()

            if existing_fixture:
                existing_fixture.league_id = league_id
                existing_fixture.home_id = home_id
                existing_fixture.away_id = away_id
                setattr(existing_fixture, 'date', date)
                setattr(existing_fixture, 'home_team_score', home_team_score)
                setattr(existing_fixture, 'away_team_score', away_team_score)
                setattr(existing_fixture, 'home_pens_score', home_pens_score)
                setattr(existing_fixture, 'away_pens_score', away_pens_score)
                setattr(existing_fixture, 'status', status)
                setattr(existing_fixture, 'round', round)
            else:
                new_fixture = Fixture(
                    id=id,
                    league_id=league_id,
                    home_id=home_id,
                    away_id=away_id,
                    date=cast(Any, date),
                    home_team_score=home_team_score,
                    away_team_score=away_team_score,
                    home_pens_score=home_pens_score,
                    away_pens_score=away_pens_score,
                    status=status,
                    round=round
                )
                db.add(new_fixture)

            await db.commit()
        except Exception as e:
            await db.rollback()
            await db.close()
            raise Exception(e)

    async def get_all_data(self, db: AsyncSession):
        """Devuelve todos los fixtures disponibles en la base de datos."""
        result = await db.execute(select(Fixture))
        return result.scalars().all()

    async def get_fixture_by_id(self, db: AsyncSession, fixture_id: int) -> Optional[Fixture]:
        """Retrieve a single fixture by its id."""
        result = await db.execute(select(Fixture).where(cast(Any, Fixture.id == fixture_id)))
        return result.scalar_one_or_none()

    async def get_fixture_with_teams(self, db: AsyncSession, fixture_id: int):
        """Retrieve a fixture and enrich it with home and away team information."""
        fixture = await self.get_fixture_by_id(db, fixture_id)
        if not fixture:
            return None

        team_service = TeamPostgres()
        home_id = getattr(fixture, 'home_id')
        away_id = getattr(fixture, 'away_id')
        home_team = await team_service.get_team_with_country_info(db, home_id)
        away_team = await team_service.get_team_with_country_info(db, away_id)

        date = getattr(fixture, 'date')
        status = getattr(fixture, 'status')

        enriched = {
            "id": getattr(fixture, 'id'),
            "league": getattr(fixture, 'league_id'),
            "home": home_team,
            "away": away_team,
            "date": date.isoformat() if date else None,
            "home_team_score": getattr(fixture, 'home_team_score'),
            "away_team_score": getattr(fixture, 'away_team_score'),
            "home_pens_score": getattr(fixture, 'home_pens_score'),
            "away_pens_score": getattr(fixture, 'away_pens_score'),
            "status": status.value if status else None,
            "round": getattr(fixture, 'round')
        }
        return enriched

    def _is_fixture_locked(self, fixture: Fixture) -> bool:
        """Determine whether predictions for this fixture should be locked.

        A fixture is considered locked if its status indicates it has started/finished
        or its scheduled date/time is in the past.
        """
        # If fixture has a status that indicates it started/finished, lock it
        status = getattr(fixture, 'status')
        if status is not None:
            finished_states = {FixtureStatus.FT, FixtureStatus.AET, FixtureStatus.PEN}
            if status in finished_states:
                return True

        # Lock if date is set and now >= fixture.date
        date = getattr(fixture, 'date')
        if date:
            try:
                return datetime.utcnow() >= date.replace(tzinfo=None)
            except Exception:
                # If date is not a datetime object or other issue, do not lock by date
                return False

        return False

    def is_fixture_started_by_date(self, fixture: Fixture) -> bool:
        """Return True if the fixture's scheduled date/time is in the past (started).

        This method intentionally ignores `status` because status values may be
        stale if the fixtures are updated only periodically. Use this when you
        need a conservative lock based solely on the scheduled start time.
        """
        date = getattr(fixture, 'date')
        if not date:
            return False
        try:
            # Compare in UTC naive to UTC naive
            return datetime.utcnow() >= date.replace(tzinfo=None)
        except Exception:
            return False

    async def get_fixtures_by_league_and_round(self, db: AsyncSession, league_id: int, round_name: str):
        """Devuelve todos los fixtures de una liga y ronda específica."""
        result = await db.execute(
            select(Fixture).where(
                cast(Any, Fixture.league_id == league_id),
                cast(Any, Fixture.round == round_name)
            )
        )
        return result.scalars().all()

    async def get_fixtures_by_league_and_round_with_teams(self, db: AsyncSession, league_id: int, round_name: str):
        """
        Devuelve todos los fixtures de una liga y ronda específica
        con la información completa de los equipos embebida.
        """
        result = await db.execute(
            select(Fixture).where(
                cast(Any, Fixture.league_id == league_id),
                cast(Any, Fixture.round == round_name)
            )
        )

        fixtures = result.scalars().all()

        team_service = TeamPostgres()
        enriched_fixtures = []

        for fixture in fixtures:
            home_id = getattr(fixture, 'home_id')
            away_id = getattr(fixture, 'away_id')
            home_team = await team_service.get_team_with_country_info(db, home_id)
            away_team = await team_service.get_team_with_country_info(db, away_id)

            date = getattr(fixture, 'date')
            status = getattr(fixture, 'status')

            enriched_fixtures.append({
                "id": getattr(fixture, 'id'),
                "league": getattr(fixture, 'league_id'),
                "home": home_team,
                "away": away_team,
                "date": date.isoformat() if date else None,
                "home_team_score": getattr(fixture, 'home_team_score'),
                "away_team_score": getattr(fixture, 'away_team_score'),
                "home_pens_score": getattr(fixture, 'home_pens_score'),
                "away_pens_score": getattr(fixture, 'away_pens_score'),
                "status": status.value if status else None,
                "round": getattr(fixture, 'round')
            })

        return enriched_fixtures