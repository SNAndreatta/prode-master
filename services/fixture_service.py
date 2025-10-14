from abc import ABC

class FixtureService(ABC):

    async def add_or_update_fixture(self):
        pass

    async def get_fixtures_by_league_and_round(self):
        pass

    async def get_fixtures_by_league_and_round_with_teams(self):
        pass
    
    async def get_all_data(self):
        pass
    
