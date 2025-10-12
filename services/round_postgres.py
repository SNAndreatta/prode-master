from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.rounds import Round

class RoundPostgres:

    async def add_round(self, db: AsyncSession, name: str, league_id: int, season: int):
        round_obj = Round(
            id=None,
            name=name,
            league_id=league_id,
            season=season
        )
        db.add(round_obj)
        await db.commit()
        await db.refresh(round_obj)
        return round_obj

    async def add_or_update_round(self, db: AsyncSession, name: str, league_id: int, season: int):
        """
        Si la ronda ya existe (por nombre, liga y temporada), la actualiza.
        Si no, la crea.
        """
        result = await db.execute(
            select(Round).where(
                Round.name == name,
                Round.league_id == league_id,
                Round.season == season
            )
        )
        existing_round = result.scalars().first()

        if existing_round:
            existing_round.name = name
            existing_round.league_id = league_id
            existing_round.season = season
            await db.commit()
            await db.refresh(existing_round)
            return existing_round
        else:
            return await self.add_round(db, name, league_id, season)

    async def add_or_skip_round(self, db: AsyncSession, name: str, league_id: int, season: int):
        """
        Si la ronda ya existe, la devuelve.
        Si no, la crea.
        """
        result = await db.execute(
            select(Round).where(
                Round.name == name,
                Round.league_id == league_id,
                Round.season == season
            )
        )
        existing_round = result.scalars().first()

        if existing_round:
            return existing_round
        else:
            return await self.add_round(db, name, league_id, season)

    async def get_all_rounds(self, db: AsyncSession):
        """
        Devuelve todas las rondas almacenadas.
        """
        result = await db.execute(select(Round))
        return result.scalars().all()

    async def get_round_by_name(self, db: AsyncSession, name: str):
        """
        Devuelve una ronda por su nombre.
        """
        result = await db.execute(select(Round).where(Round.name == name))
        return result.scalars().first()

    async def get_rounds_by_league(self, db: AsyncSession, league_id: int, season: int | None = None):
        """
        Devuelve todas las rondas de una liga, opcionalmente filtradas por temporada.
        """
        query = select(Round).where(Round.league_id == league_id)
        if season is not None:
            query = query.where(Round.season == season)

        result = await db.execute(query)
        return result.scalars().all()

    def rounds_to_json(self, rounds: list[Round]):
        """
        Convierte una lista de rondas en una lista de JSONs.
        """
        return [r.to_json() for r in rounds]
