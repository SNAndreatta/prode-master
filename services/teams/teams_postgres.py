from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.teams.teams import Team

class TeamPostgres:
    async def add_team(self, db: AsyncSession, id: int, name: str, country_name: str, logo: str = None):
        team = Team(id=id, name=name, country_name=country_name, logo=logo)
        db.add(team)
        await db.commit()
        return team

    async def add_or_update_team(self, db: AsyncSession, id: int, name: str, country_name: str, logo: str = None):
        # Check if the team exists
        result = await db.execute(select(Team).where(Team.id == id))
        existing_team = result.scalars().first()

        if existing_team:
            # Update the existing team
            existing_team.name = name
            existing_team.country_name = country_name
            existing_team.logo = logo
            await db.commit()
            return existing_team
        else:
            # Add a new team
            return await self.add_team(db, id, name, country_name, logo)

    async def add_or_skip_team(self, db: AsyncSession, id: int, name: str, country_name: str, logo: str = None):
        # Check if the team exists
        result = await db.execute(select(Team).where(Team.id == id))
        existing_team = result.scalars().first()

        if existing_team:
            # Skip adding the team
            return existing_team
        else:
            # Add a new team
            return await self.add_team(db, id, name, country_name, logo)

    def teams_to_json(self, teams: list[Team]):
        return [
            {"id": t.id, "name": t.name, "country_name": t.country_name, "logo": t.logo}
            for t in teams
        ]