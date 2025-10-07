from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.leagues.leagues import League

class LeaguePostgres:
    async def add_league(self, db: AsyncSession, id: int, name: str, country_name: str, logo: str = None):
        league = League(id=id, name=name, country_name=country_name, logo=logo)
        db.add(league)
        await db.commit()
        return league

    async def add_or_update_league(self, db: AsyncSession, id: int, name: str, country_name: str, logo: str = None):
        # Check if the league exists
        result = await db.execute(select(League).where(League.id == id))
        existing_league = result.scalars().first()

        if existing_league:
            # Update the existing league
            existing_league.name = name
            existing_league.country_name = country_name
            existing_league.logo = logo
            await db.commit()
            return existing_league
        else:
            # Add a new league
            return await self.add_league(db, id, name, country_name, logo)

    async def add_or_skip_league(self, db: AsyncSession, id: int, name: str, country_name: str, logo: str = None):
        # Check if the league exists
        result = await db.execute(select(League).where(League.id == id))
        existing_league = result.scalars().first()

        if existing_league:
            # Skip adding the league
            return existing_league
        else:
            # Add a new league
            return await self.add_league(db, id, name, country_name, logo)

    async def get_all_leagues(self, db: AsyncSession):
        result = await db.execute(select(League))
        return result.scalars().all()
    
    def leagues_to_json(self, leagues: list[League]):
        return [
            {"id": l.id, "name": l.name, "country_name": l.country_name, "logo": l.logo}
            for l in leagues
        ]
    
    async def get_leagues_by_country(self, db: AsyncSession, country_name: str):
        result = await db.execute(
            select(League).where(League.country_name == country_name)
        )
        return result.scalars().all()