import logging
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from core.api_connection import apiFutbolServicio
from services.fixture_postgres import FixturePostgres
from services.leagues_postgres import LeaguePostgres
from models.fixtures.fixture_status import string_to_enum
from datetime import datetime, timezone, timedelta

async def get_fixtures(api_endpoint: str, db: AsyncSession, arg_timezone, load_last_run_datetime, save_last_run_datetime):
    logger = logging.getLogger("fixtures_AF_logger")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)

    apiFutbol = apiFutbolServicio(endpoint=api_endpoint)
    league_postgres = LeaguePostgres()
    fixture_postgres = FixturePostgres()

    # Determine date range
    last_run = load_last_run_datetime()
    start_date = last_run.date().isoformat() if last_run else datetime.now(arg_timezone).date().isoformat()
    end_date = (datetime.fromisoformat(start_date) + timedelta(days=30)).date().isoformat()

    logger.info(f"Fetching fixtures from {start_date} to {end_date}...")

    try:
        leagues = await league_postgres.get_all_leagues(db)
        if not leagues:
            raise Exception("No leagues found in database")
        logger.info(f"Retrieved {len(leagues)} leagues from the database.")

        added_count = 0
        failed_count = 0
        failed_fixtures = []

        for league in leagues:
            try:
                logger.info(f"Fetching fixtures for league: {league.name}")
                season = league.season

                try:
                    respuesta = apiFutbol.fixtures_from_api(
                        liga=league.id,
                        season=season,
                        from_d=start_date,
                        to=end_date
                    )
                    if respuesta:
                        logger.info(f"Received {len(respuesta)} fixtures for {league.name} season {season}.")
                except requests.RequestException as e:
                    logger.warning(f"Error fetching fixtures for {league.name}: {e}")
                    continue

                if not respuesta:
                    logger.warning(f"No fixtures found for {league.name}, skipping.")
                    continue

                for item in respuesta:
                    try:
                        fixture_data = item.get("fixture", {})
                        league_data = item.get("league", {})
                        teams_data = item.get("teams", {})
                        goals_data = item.get("goals", {})
                        score_data = item.get("score", {})

                        fixture_id = fixture_data.get("id")
                        round = league_data.get("round")

                        date_str = fixture_data.get("date")
                        date = None
                        if date_str:
                            try:
                                local_dt = datetime.fromisoformat(date_str)
                                date = local_dt.astimezone(timezone.utc)
                            except Exception as e:
                                logger.warning(f"Invalid date format: {date_str} - {e}")

                        status_enum = string_to_enum(fixture_data.get("status", {}).get("short"))
                        home_team = teams_data.get("home", {})
                        away_team = teams_data.get("away", {})
                        home_id = home_team.get("id")
                        away_id = away_team.get("id")
                        home_score = goals_data.get("home")
                        away_score = goals_data.get("away")
                        home_pen_score = score_data.get("penalty", {}).get("home") if score_data.get("penalty") else None
                        away_pen_score = score_data.get("penalty", {}).get("away") if score_data.get("penalty") else None

                        if not all([fixture_id, league_data.get("id"), home_id, away_id]):
                            logger.warning(f"Invalid fixture data: {item}")
                            failed_count += 1
                            failed_fixtures.append(item)
                            continue

                        await fixture_postgres.add_or_update_fixture(
                            db=db,
                            id=fixture_id,
                            league_id=league_data.get("id"),
                            home_id=home_id,
                            away_id=away_id,
                            date=date,
                            home_team_score=home_score,
                            away_team_score=away_score,
                            home_pens_score=home_pen_score,
                            away_pens_score=away_pen_score,
                            status=status_enum,
                            round=round
                        )

                        added_count += 1
                        logger.info(f"Added/updated fixture {fixture_id} ({league_data.get('name')})")

                    except Exception as ex:
                        failed_count += 1
                        failed_fixtures.append(item)
                        logger.exception(f"Error adding fixture {fixture_data.get('id')}: {ex}")

            except Exception as league_error:
                logger.exception(f"Unexpected error processing league {league.name}: {league_error}")
                continue

        logger.info(f"Fixtures process completed: added={added_count}, failed={failed_count}")

        save_last_run_datetime(datetime.now(arg_timezone))

        return {
            "status": "success",
            "fixtures_added": added_count,
            "fixtures_failed": failed_count,
            "failed_fixtures": failed_fixtures,
        }

    except Exception as e:
        logger.exception(f"Unexpected server error: {e}")
        raise e
