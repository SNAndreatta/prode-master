from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.leagues import League
from services.country_postgres import CountryPostgres

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

    def leagues_to_json(self, leagues: list[League]):
        return [
            league.to_json()
            for league in leagues
        ]

    async def get_league_by_id(self, db: AsyncSession, id: int):
        result = await db.execute(select(League).where(League.id == id))
        return result.scalar_one_or_none()

    async def get_leagues_by_country(self, db: AsyncSession, country_name: str):
        result = await db.execute(
            select(League).where(League.country_name == country_name)
        )
        return result.scalars().all()

    async def get_all_leagues_with_country_info(self, db: AsyncSession):
        """
        Devuelve todas las ligas con la información completa del país embebida.
        """
        result = await db.execute(select(League))
        leagues = result.scalars().all()

        country_service = CountryPostgres()
        enriched_leagues = []

        for league in leagues:
            country = await country_service.get_country_by_name(db, league.country_name)
            if country:
                enriched_leagues.append({
                    "id": league.id,
                    "name": league.name,
                    "logo": league.logo,
                    "season": league.season,
                    "country": country.to_json()
                })
            else:
                # En caso de que no exista el país (por integridad)
                enriched_leagues.append({
                    "id": league.id,
                    "name": league.name,
                    "logo": league.logo,
                    "season": league.season,
                    "country": {
                        "name": league.country_name,
                        "code": None,
                        "flag": None
                    }
                })

        return enriched_leagues
    
    async def get_all_countries_with_league(self, db: AsyncSession):
        country_service = CountryPostgres()

        leagues = await self.get_all_leagues(db)
        countries = []
        for league in leagues:
            country = await country_service.get_country_by_name(db, league.country_name)
            if country and country not in countries:
                countries.append(country)
        return countries