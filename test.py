import asyncio
from services.fixture_valkey import FixtureValkey
import valkey
from settings import VALKEY_URI

valkey_client = valkey.from_url(VALKEY_URI)
fv = FixtureValkey(valkey_client=valkey_client)

async def add_fixture():
    print("pija")
    response = await fv.add_or_update_fixture()  # call get_all_data, not add_or_update_fixture
    print("response:", response)

async def get_fixture():
    print("niga")
    response = await fv.get_all_data()  # call get_all_data, not add_or_update_fixture
    print("response:", response)

async def get_fixtures_by_league_and_round():
    print("sibidi")
    response = await fv.get_fixtures_by_league_and_round(league_id=2, round_name="1st Qualifying Round")  # call get_all_data, not add_or_update_fixture
    print("response:", response)

asyncio.run(get_fixtures_by_league_and_round())
