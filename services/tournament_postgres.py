from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from models.tournaments import Tournament
from models.leagues import League
from models.auth.auth_models import User
from typing import List, Optional
import logging

logger = logging.getLogger("tournament_service")

class TournamentPostgres:
    """Service class for tournament database operations"""

    async def create_tournament(
        self, 
        db: AsyncSession, 
        name: str, 
        creator_id: int, 
        league_id: int,
        description: str = None,
        is_public: bool = True,
        max_participants: int = 100
    ) -> Tournament:
        """Create a new tournament"""
        try:
            # Verify that the league exists
            league = await db.scalar(select(League).where(League.id == league_id))
            if not league:
                raise ValueError(f"League with id {league_id} not found")
            
            # Verify that the creator exists
            creator = await db.scalar(select(User).where(User.id == creator_id))
            if not creator:
                raise ValueError(f"User with id {creator_id} not found")

            tournament = Tournament(
                name=name,
                creator_id=creator_id,
                league_id=league_id,
                description=description,
                is_public=is_public,
                max_participants=max_participants
            )
            
            db.add(tournament)
            await db.commit()
            await db.refresh(tournament)
            
            logger.info(f"Tournament created successfully: {tournament.name} (id: {tournament.id})")
            return tournament
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating tournament: {e}")
            raise e

    async def get_public_tournaments(self, db: AsyncSession) -> List[Tournament]:
        """Get all public tournaments"""
        try:
            result = await db.execute(
                select(Tournament)
                .where(Tournament.is_public == True)
                .order_by(Tournament.created_at.desc())
            )
            tournaments = result.scalars().all()
            
            logger.info(f"Retrieved {len(tournaments)} public tournaments")
            return list(tournaments)
            
        except Exception as e:
            logger.error(f"Error fetching public tournaments: {e}")
            raise e

    async def get_tournament_by_id(self, db: AsyncSession, tournament_id: int) -> Optional[Tournament]:
        """Get a tournament by its ID"""
        try:
            result = await db.execute(
                select(Tournament).where(Tournament.id == tournament_id)
            )
            tournament = result.scalar_one_or_none()
            
            if tournament:
                logger.info(f"Tournament found: {tournament.name} (id: {tournament.id})")
            else:
                logger.info(f"Tournament not found with id: {tournament_id}")
                
            return tournament
            
        except Exception as e:
            logger.error(f"Error fetching tournament by id {tournament_id}: {e}")
            raise e

    async def get_tournaments_by_creator(self, db: AsyncSession, creator_id: int) -> List[Tournament]:
        """Get all tournaments created by a specific user"""
        try:
            result = await db.execute(
                select(Tournament)
                .where(Tournament.creator_id == creator_id)
                .order_by(Tournament.created_at.desc())
            )
            tournaments = result.scalars().all()
            
            logger.info(f"Retrieved {len(tournaments)} tournaments for creator {creator_id}")
            return list(tournaments)
            
        except Exception as e:
            logger.error(f"Error fetching tournaments for creator {creator_id}: {e}")
            raise e

    async def get_tournaments_by_league(self, db: AsyncSession, league_id: int) -> List[Tournament]:
        """Get all public tournaments for a specific league"""
        try:
            result = await db.execute(
                select(Tournament)
                .where(Tournament.league_id == league_id, Tournament.is_public == True)
                .order_by(Tournament.created_at.desc())
            )
            tournaments = result.scalars().all()
            
            logger.info(f"Retrieved {len(tournaments)} public tournaments for league {league_id}")
            return list(tournaments)
            
        except Exception as e:
            logger.error(f"Error fetching tournaments for league {league_id}: {e}")
            raise e

    async def update_tournament(
        self, 
        db: AsyncSession, 
        tournament_id: int, 
        creator_id: int,
        **kwargs
    ) -> Optional[Tournament]:
        """Update a tournament (only by its creator)"""
        try:
            # First verify the tournament exists and belongs to the creator
            tournament = await self.get_tournament_by_id(db, tournament_id)
            if not tournament:
                raise ValueError(f"Tournament with id {tournament_id} not found")
            
            if tournament.creator_id != creator_id:
                raise ValueError("Only the tournament creator can update the tournament")

            # Update only provided fields
            update_data = {k: v for k, v in kwargs.items() if v is not None}
            if not update_data:
                return tournament

            await db.execute(
                update(Tournament)
                .where(Tournament.id == tournament_id)
                .values(**update_data)
            )
            await db.commit()
            
            # Return updated tournament
            updated_tournament = await self.get_tournament_by_id(db, tournament_id)
            logger.info(f"Tournament updated successfully: {updated_tournament.name} (id: {tournament_id})")
            return updated_tournament
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating tournament {tournament_id}: {e}")
            raise e

    async def delete_tournament(self, db: AsyncSession, tournament_id: int, creator_id: int) -> bool:
        """Delete a tournament (only by its creator)"""
        try:
            # First verify the tournament exists and belongs to the creator
            tournament = await self.get_tournament_by_id(db, tournament_id)
            if not tournament:
                raise ValueError(f"Tournament with id {tournament_id} not found")
            
            if tournament.creator_id != creator_id:
                raise ValueError("Only the tournament creator can delete the tournament")

            await db.execute(
                delete(Tournament).where(Tournament.id == tournament_id)
            )
            await db.commit()
            
            logger.info(f"Tournament deleted successfully: {tournament.name} (id: {tournament_id})")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting tournament {tournament_id}: {e}")
            raise e

    def tournaments_to_json(self, tournaments: List[Tournament]) -> List[dict]:
        """Convert a list of tournaments to JSON format"""
        return [tournament.to_json() for tournament in tournaments]
