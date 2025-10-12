from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.teams import Team
from services.country_postgres import CountryPostgres

class TeamPostgres:
    async def add_team(self, db: AsyncSession, id: int, name: str, country_name: str, logo: str = None):
        team = Team(id=id, name=name, country_name=country_name, logo=logo)
        db.add(team)
        await db.commit()
        return team

    async def add_or_update_team(self, db: AsyncSession, id: int, name: str, country_name: str, logo: str = None):
        result = await db.execute(select(Team).where(Team.id == id))
        existing_team = result.scalars().first()

        if existing_team:
            existing_team.name = name
            existing_team.country_name = country_name
            existing_team.logo = logo
            await db.commit()
            return existing_team
        else:
            return await self.add_team(db, id, name, country_name, logo)

    async def add_or_skip_team(self, db: AsyncSession, id: int, name: str, country_name: str, logo: str = None):
        result = await db.execute(select(Team).where(Team.id == id))
        existing_team = result.scalars().first()

        if existing_team:
            return existing_team
        else:
            return await self.add_team(db, id, name, country_name, logo)
    
    def teams_to_json(self, teams: list[Team]):
        return [
            team.to_json()
            for team in teams
        ]
    
    async def get_team_by_id(self, db: AsyncSession, id: int):
        result = await db.execute(select(Team).where(Team.id == id))
        return result.scalar_one_or_none()

    async def get_team_with_country_info(self, db: AsyncSession, id: int):
        """
        Devuelve un equipo con la información del país embebida.
        """
        result = await db.execute(select(Team).where(Team.id == id))
        team = result.scalar_one_or_none()

        country_service = CountryPostgres()
        if team:
            country = await country_service.get_country_by_name(db, team.country_name)
            if country:
                return {
                    "id": team.id,
                    "name": team.name,
                    "logo": team.logo,
                    "country": country.to_json()
                }
            else:
                return {
                    "id": team.id,
                    "name": team.name,
                    "logo": team.logo,
                    "country": {
                        "name": team.country_name,
                        "code": None,
                        "flag": None
                    }
                }
        else:
            return None

    async def get_all_teams_with_country_info(self, db: AsyncSession):
        """
        Devuelve todos los equipos con la información del país embebida.
        """
        result = await db.execute(select(Team))
        teams = result.scalars().all()

        country_service = CountryPostgres()
        enriched_teams = []

        for team in teams:
            country = await country_service.get_country_by_name(db, team.country_name)

            if country:
                enriched_teams.append({
                    "id": team.id,
                    "name": team.name,
                    "logo": team.logo,
                    "country": country.to_json()
                })
            else:
                enriched_teams.append({
                    "id": team.id,
                    "name": team.name,
                    "logo": team.logo,
                    "country": {
                        "name": team.country_name,
                        "code": None,
                        "flag": None
                    }
                })

        return enriched_teams