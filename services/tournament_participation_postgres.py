import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, and_
from models.tournament_participants import TournamentParticipant
from models.tournaments import Tournament
from models.auth.auth_models import User
from datetime import datetime

logger = logging.getLogger("tournament_participation_service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

class TournamentParticipationPostgres:
    async def join_tournament(
        self,
        db: AsyncSession,
        tournament_id: int,
        user_id: int
    ) -> TournamentParticipant:
        """Add a user to a tournament"""
        # Check if user is already a participant
        existing_participation = await db.scalar(
            select(TournamentParticipant).where(
                and_(
                    TournamentParticipant.tournament_id == tournament_id,
                    TournamentParticipant.user_id == user_id
                )
            )
        )
        
        if existing_participation:
            raise ValueError("User is already a participant in this tournament")
        
        # Create new participation
        participation = TournamentParticipant(
            tournament_id=tournament_id,
            user_id=user_id
        )
        
        db.add(participation)
        await db.commit()
        await db.refresh(participation)
        
        logger.info(f"User {user_id} joined tournament {tournament_id}")
        return participation

    async def leave_tournament(
        self,
        db: AsyncSession,
        tournament_id: int,
        user_id: int
    ) -> bool:
        """Remove a user from a tournament"""
        result = await db.execute(
            delete(TournamentParticipant).where(
                and_(
                    TournamentParticipant.tournament_id == tournament_id,
                    TournamentParticipant.user_id == user_id
                )
            )
        )
        await db.commit()
        
        if result.rowcount > 0:
            logger.info(f"User {user_id} left tournament {tournament_id}")
            return True
        else:
            logger.warning(f"User {user_id} was not a participant in tournament {tournament_id}")
            return False

    async def remove_participant(
        self,
        db: AsyncSession,
        tournament_id: int,
        user_id: int
    ) -> bool:
        """Remove a specific user from a tournament (creator/admin only)"""
        result = await db.execute(
            delete(TournamentParticipant).where(
                and_(
                    TournamentParticipant.tournament_id == tournament_id,
                    TournamentParticipant.user_id == user_id
                )
            )
        )
        await db.commit()
        
        if result.rowcount > 0:
            logger.info(f"User {user_id} removed from tournament {tournament_id}")
            return True
        else:
            logger.warning(f"User {user_id} was not a participant in tournament {tournament_id}")
            return False

    async def get_tournament_participants(
        self,
        db: AsyncSession,
        tournament_id: int
    ) -> list[TournamentParticipant]:
        """Get all participants of a tournament"""
        result = await db.execute(
            select(TournamentParticipant, User)
            .join(User, TournamentParticipant.user_id == User.id)
            .where(TournamentParticipant.tournament_id == tournament_id)
            .order_by(TournamentParticipant.joined_at)
        )
        
        participants = []
        for participation, user in result:
            # Create a combined object for easier access
            participation.user = user
            participants.append(participation)
        
        logger.info(f"Retrieved {len(participants)} participants for tournament {tournament_id}")
        return participants

    async def is_participant(
        self,
        db: AsyncSession,
        tournament_id: int,
        user_id: int
    ) -> bool:
        """Check if a user is a participant in a tournament"""
        result = await db.scalar(
            select(TournamentParticipant).where(
                and_(
                    TournamentParticipant.tournament_id == tournament_id,
                    TournamentParticipant.user_id == user_id
                )
            )
        )
        return result is not None

    async def get_tournament_by_id(
        self,
        db: AsyncSession,
        tournament_id: int
    ) -> Tournament | None:
        """Get tournament by ID"""
        result = await db.scalar(
            select(Tournament).where(Tournament.id == tournament_id)
        )
        return result

    async def delete_tournament(
        self,
        db: AsyncSession,
        tournament_id: int
    ) -> bool:
        """Delete a tournament (cascade deletes participants)"""
        result = await db.execute(
            delete(Tournament).where(Tournament.id == tournament_id)
        )
        await db.commit()
        
        if result.rowcount > 0:
            logger.info(f"Tournament {tournament_id} deleted successfully")
            return True
        else:
            logger.warning(f"Tournament {tournament_id} not found")
            return False

    async def update_tournament_visibility(
        self,
        db: AsyncSession,
        tournament_id: int,
        is_public: bool
    ) -> Tournament | None:
        """Update tournament visibility"""
        from sqlalchemy import update
        
        stmt = (
            update(Tournament)
            .where(Tournament.id == tournament_id)
            .values(is_public=is_public, updated_at=datetime.utcnow())
        )
        
        await db.execute(stmt)
        await db.commit()
        
        # Return updated tournament
        return await self.get_tournament_by_id(db, tournament_id)
