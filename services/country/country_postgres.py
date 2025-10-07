from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.countries.countries import Country
from services.country.country_interface import CountryService

class CountryPostgres(CountryService):
    
    async def add_country(self, db: AsyncSession, name: str, code: str, flag: str):
        country = Country(name=name, code=code, flag=flag)
        db.add(country)
        await db.commit()
        return country

    async def add_or_update_country(self, db: AsyncSession, name: str, code: str, flag: str):
        # Check if the country exists
        result = await db.execute(select(Country).where(Country.code == code))
        existing_country = result.scalars().first()

        if existing_country:
            # Update the existing country
            existing_country.name = name
            existing_country.flag = flag
            await db.commit()
            return existing_country
        else:
            # Add a new country
            return await self.add_country(db, name, code, flag)

    async def add_or_skip_country(self, db: AsyncSession, name: str, code: str, flag: str):
        # Check if the country exists
        result = await db.execute(select(Country).where(Country.code == code))
        existing_country = result.scalars().first()

        if existing_country:
            # Skip adding the country
            return existing_country
        else:
            # Add a new country
            return await self.add_country(db, name, code, flag)