import json
import logging
from database import get_db  # your async session provider
from services.fixture_postgres import FixturePostgres
from services.fixture_service import FixtureService

logger = logging.getLogger(__name__)

class FixtureValkey(FixtureService):
    def __init__(self, valkey_client):
        self.valkey_client = valkey_client  # sync valkey client or async if available

    def _fixture_key(self, fixture_id: int):
        return f"fixture:{fixture_id}"

    def _league_round_key(self, league_id: int, round_name: str):
        return f"fixtures:{league_id}:{round_name}"

    async def get_all_data(self, include_league_round_sets=False):
        """
        Retrieve all fixture data from Valkey
        
        Args:
            include_league_round_sets: If True, also retrieves league-round set information
        
        Returns: Dictionary with fixtures and optionally league-round sets
        """
        print("🚀 Starting to retrieve all fixture data from Valkey")
        
        try:
            result = {"fixtures": []}
            
            # Get all fixture keys
            print("🔍 Scanning for fixture keys...")
            fixture_keys = []
            cursor = 0
            
            while True:
                cursor, keys = self.valkey_client.scan(cursor, match="fixture:*", count=100)
                fixture_keys.extend(keys)
                #print(f"📋 Found {len(keys)} keys in this scan, total: {len(fixture_keys)}")
                if cursor == 0:
                    break
            
            #print(f"📊 Total fixture keys found: {len(fixture_keys)}")
            
            if not fixture_keys:
                print("⚠️ No fixture keys found in Valkey")
                return result
            
            # Retrieve all fixture data
            all_fixtures = []
            batch_size = 100
            
            for i in range(0, len(fixture_keys), batch_size):
                batch_keys = fixture_keys[i:i + batch_size]
                batch_num = i//batch_size + 1
                total_batches = (len(fixture_keys)-1)//batch_size + 1
                #print(f"📥 Retrieving batch {batch_num}/{total_batches} ({len(batch_keys)} fixtures)")
                
                pipeline = self.valkey_client.pipeline()
                for key in batch_keys:
                    pipeline.get(key)
                batch_results = pipeline.execute()
                
                for key, fixture_json in zip(batch_keys, batch_results):
                    if fixture_json:
                        try:
                            fixture_data = json.loads(fixture_json)
                            all_fixtures.append(fixture_data)
                        except json.JSONDecodeError as e:
                            print(f"❌ Failed to parse JSON for key {key}: {e}")
                    else:
                        print(f"⚠️ No data found for key {key}")
            
            result["fixtures"] = all_fixtures
            print(f"✅ Successfully retrieved {len(all_fixtures)} fixtures")
            
            # Optionally get league-round sets
            if include_league_round_sets:
                print("🔍 Scanning for league-round sets...")
                result["league_round_sets"] = await self._get_all_league_round_sets()
            
            print("🏁 Data retrieval completed successfully")
            return result
        
        except Exception as e:
            print(f"💥 Error retrieving data from Valkey: {str(e)}")
            print("Full traceback:")
            import traceback
            traceback.print_exc()
            raise

    async def add_or_update_fixture(self):
        print("add_or_update_fixture")
        print("🚀 Starting fixture data sync from PostgreSQL to Valkey")
        
        fixture_postgres = FixturePostgres()
        try:
            print("📡 Connecting to database...")
            async for db in get_db():
                print("✅ Database connection established")
                
                print("📥 Fetching all fixtures from PostgreSQL...")
                fixtures = await fixture_postgres.get_all_data(db)
                print(f"📊 Retrieved {len(fixtures)} fixtures from database")
                
                if not fixtures:
                    print("⚠️ No fixtures found in database")
                    return "0 fixtures synced to Valkey"
                
                # Save each fixture to Valkey
                processed_count = 0
                for i, f in enumerate(fixtures, 1):
                    if i % 100 == 0 or i == len(fixtures):
                        print(f"🔄 Processing fixture {i}/{len(fixtures)} ({(i/len(fixtures))*100:.1f}%)")
                    
                    fixture_data = {
                        "id": f.id,
                        "league_id": f.league_id,
                        "home_id": f.home_id,
                        "away_id": f.away_id,
                        "date": f.date.isoformat() if f.date else None,
                        "home_team_score": f.home_team_score,
                        "away_team_score": f.away_team_score,
                        "home_pens_score": f.home_pens_score,
                        "away_pens_score": f.away_pens_score,
                        "status": f.status.value if f.status else None,
                        "round": f.round
                    }

                    key = self._fixture_key(f.id)
                    self.valkey_client.set(key, json.dumps(fixture_data))

                    league_round_key = self._league_round_key(f.league_id, f.round)
                    self.valkey_client.sadd(league_round_key, f.id)
                    
                    processed_count += 1
                
                print(f"✅ Successfully processed {processed_count} fixtures")
                print(f"📝 Created/updated {processed_count} fixture keys in Valkey")
                print("🏁 Fixture sync completed successfully")
                
                return f"{len(fixtures)} fixtures synced to Valkey"
                
        except Exception as e:
            print(f"💥 Error during fixture sync: {str(e)}")
            print("Full traceback:")
            raise
