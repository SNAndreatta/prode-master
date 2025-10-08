from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.leagues.leagues import League


class LeaguePostgres:
    async def add_league(
        self, 
        db: AsyncSession, 
        id: int, 
        name: str, 
        country_name: str, 
        season: int, 
        logo: str = None
    ):
        """Adds a new league entry into the database."""
        league = League(id=id, name=name, country_name=country_name, season=season, logo=logo)
        db.add(league)
        await db.commit()
        return league

    async def add_or_update_league(
        self, 
        db: AsyncSession, 
        id: int, 
        name: str, 
        country_name: str, 
        season: int, 
        logo: str = None
    ):
        """
        Adds or updates a league depending on whether it already exists.
        League uniqueness is based on both 'id' and 'season'.
        """
        result = await db.execute(
            select(League).where(League.id == id, League.season == season)
        )
        existing_league = result.scalars().first()

        if existing_league:
            existing_league.name = name
            existing_league.country_name = country_name
            existing_league.logo = logo
            await db.commit()
            return existing_league
        else:
            return await self.add_league(db, id, name, country_name, season, logo)

    async def add_or_skip_league(
        self, 
        db: AsyncSession, 
        id: int, 
        name: str, 
        country_name: str, 
        season: int, 
        logo: str = None
    ):
        """
        Adds a new league only if it doesn't exist for that season.
        If it exists, skip adding.
        """
        result = await db.execute(
            select(League).where(League.id == id, League.season == season)
        )
        existing_league = result.scalars().first()

        if existing_league:
            return existing_league
        else:
            return await self.add_league(db, id, name, country_name, season, logo)

    async def get_all_leagues(self, db: AsyncSession):
        result = await db.execute(select(League))
        return result.scalars().all()

    def league_to_json(self, league: League):
        return {
            "id": league.id,
            "name": league.name,
            "country_name": league.country_name,
            "logo": league.logo,
            "season": league.season,
        }

    def leagues_to_json(self, leagues: list[League]):
        return [
            {
                "id": l.id,
                "name": l.name,
                "country_name": l.country_name,
                "logo": l.logo,
                "season": l.season,
            }
            for l in leagues
        ]

    async def get_leagues_by_country(self, db: AsyncSession, country_name: str):
        result = await db.execute(
            select(League).where(League.country_name == country_name)
        )
        return result.scalars().all()
