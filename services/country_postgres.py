from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.countries import Country
from services.leagues_postgres import LeaguePostgres

class CountryPostgres():
    
    async def add_country(self, db: AsyncSession, name: str, code: str, flag: str):
        country = Country(name=name, code=code, flag=flag)
        db.add(country)
        await db.commit()
        return country

    async def add_or_update_country(self, db: AsyncSession, name: str, code: str, flag: str):
        result = await db.execute(select(Country).where(Country.code == code))
        existing_country = result.scalars().first()

        if existing_country:
            existing_country.name = name
            existing_country.flag = flag
            await db.commit()
            return existing_country
        else:
            return await self.add_country(db, name, code, flag)

    async def add_or_skip_country(self, db: AsyncSession, name: str, code: str, flag: str):
        result = await db.execute(select(Country).where(Country.code == code))
        existing_country = result.scalars().first()

        if existing_country:
            return existing_country
        else:
            return await self.add_country(db, name, code, flag)

    async def get_all_countries(self, db: AsyncSession):
        result = await db.execute(select(Country))
        return result.scalars().all()

    async def get_country_by_name(self, db: AsyncSession, name: str):
        result = await db.execute(select(Country).where(Country.name == name))
        return result.scalars().first()
    
    async def get_all_countries_with_league(self, db: AsyncSession):
        league_service = LeaguePostgres()
        leagues = await league_service.get_all_leagues(db)
        countries = []
        for league in leagues:
            country = await self.get_country_by_name(db, league.country_name)
            if country and country not in countries:
                countries.append(country)
        return countries

    def countries_to_json(self, countries: list[Country]):
        return [
            country.to_json()
            for country in countries
        ]