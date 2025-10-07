from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.countries.countries import Country

class CountryPostgres():
    
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

    async def get_all_countries(self, db: AsyncSession):
        result = await db.execute(select(Country))
        return result.scalars().all()

    async def get_country_by_name(self, db: AsyncSession, name: str):
        result = await db.execute(select(Country).where(Country.name == name))
        return result.scalars().first()