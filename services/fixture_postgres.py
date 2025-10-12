from models.fixture import Fixture
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.fixture_status import FixtureStatus

class FixturePostgres:
    async def add_or_update_fixture(
        self,
        db: AsyncSession,
        id: int,
        league_id: int,
        home_id: int,
        away_id: int,
        date: str,
        home_team_score: int,
        away_team_score: int,
        home_pens_score: int,
        away_pens_score: int,
        status: FixtureStatus,
        round: str
    ):
        try:
            existing_fixture = await db.execute(select(Fixture).filter(Fixture.id == id))
            existing_fixture = existing_fixture.scalar_one_or_none()

            if existing_fixture:
                existing_fixture.league_id = league_id
                existing_fixture.home_id = home_id
                existing_fixture.away_id = away_id
                existing_fixture.date = date
                existing_fixture.home_team_score = home_team_score
                existing_fixture.away_team_score = away_team_score
                existing_fixture.home_pens_score = home_pens_score
                existing_fixture.away_pens_score = away_pens_score
                existing_fixture.status = status
                existing_fixture.round = round
            else:
                new_fixture = Fixture(
                    id=id,
                    league_id=league_id,
                    home_id=home_id,
                    away_id=away_id,
                    date=date,
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