from models.fixtures.fixture import Fixture
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.fixtures.fixture_status import FixtureStatus
from services.teams_postgres import TeamPostgres

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

    async def get_all_data(self, db: AsyncSession):
        """Devuelve todos los fixtures disponibles en la base de datos."""
        result = await db.execute(select(Fixture))
        return result.scalars().all()

    async def get_fixtures_by_league_and_round(self, db: AsyncSession, league_id: int, round_name: str):
        """Devuelve todos los fixtures de una liga y ronda específica."""
        result = await db.execute(
            select(Fixture).where(
                Fixture.league_id == league_id,
                Fixture.round == round_name
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
                    Fixture.league_id == league_id,
                    Fixture.round == round_name
                )
            )

            fixtures = result.scalars().all()

            team_service = TeamPostgres()
            enriched_fixtures = []

            for fixture in fixtures:
                home_team = await team_service.get_team_with_country_info(db, fixture.home_id)
                away_team = await team_service.get_team_with_country_info(db, fixture.away_id)

                enriched_fixtures.append({
                    "id": fixture.id,
                    "league": fixture.league_id,
                    "home": home_team,
                    "away": away_team,
                    "date": fixture.date.isoformat(),
                    "home_team_score": fixture.home_team_score,
                    "away_team_score": fixture.away_team_score,
                    "home_pens_score": fixture.home_pens_score,
                    "away_pens_score": fixture.away_pens_score,
                    "status": fixture.status.value if fixture.status else None,
                    "round": fixture.round
                })

            return enriched_fixtures