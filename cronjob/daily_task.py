from cronjob.api_football.countries import get_countries
from cronjob.api_football.fixtures import get_fixtures
from cronjob.api_football.leagues import get_leagues
from cronjob.api_football.round import get_rounds
from cronjob.api_football.teams import get_teams
from dotenv import load_dotenv
import os
from database import get_db

async def update_database(arg_timezone, load_last_run_datetime, save_last_run_datetime):
    load_dotenv()
    api = os.getenv("API_ENDPOINT")
    async for bd in get_db():
        db = bd
    
    # await get_countries(api, db)
    # await get_leagues(api, db)
    await get_rounds(api, db)
    # await get_teams(api, db)
    await get_fixtures(api_endpoint=api, db=db, arg_timezone=arg_timezone, load_last_run_datetime=load_last_run_datetime, save_last_run_datetime=save_last_run_datetime) 