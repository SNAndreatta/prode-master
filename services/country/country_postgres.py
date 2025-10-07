from sqlalchemy.ext.asyncio import AsyncSession
from models.countries.countries import Country
from services.country.country_interface import CountryService

class CountryPostgres(CountryService):
    
    async def add_country(self, db: AsyncSession , name:str, code:str, flag:str):
        country = Country(name, code, flag)
        db.flag(country)
        await db.flush()
        await db.refresh()
        return country
        