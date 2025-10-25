import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from services.tournament_postgres import TournamentPostgres
from services.tournament_participation_postgres import TournamentParticipationPostgres
from services.leagues_postgres import LeaguePostgres
from models.auth.auth_models import User
from blueprints.auth.jwt_handler import decode_jwt
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from schemas.tournament_schemas import (
    TournamentJoinResponse,
    TournamentLeaveResponse,
    TournamentDeleteResponse,
    RemoveParticipantResponse,
    ParticipantOut,
    TournamentInviteRequest,
    TournamentVisibilityRequest,
    TournamentInviteResponse,
    TournamentVisibilityResponse
)

# Request model for partial updates
class TournamentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None
    max_participants: Optional[int] = Field(None, ge=2, le=1000)

# Pydantic models for request/response
class TournamentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Tournament name")
    description: Optional[str] = Field(None, max_length=500, description="Tournament description")
    league_id: int = Field(..., description="League ID this tournament is associated with")
    is_public: bool = Field(True, description="Whether the tournament is public")
    max_participants: int = Field(100, ge=2, le=1000, description="Maximum number of participants")

class TournamentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_public: bool
    creator_id: int
    league_id: int
    max_participants: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Dependency to get current user from JWT token
async def get_current_user(
    authorization: str = Header(..., description="Bearer token"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extract and validate user from JWT token"""
    try:
        # Extract token from "Bearer <token>" format
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        token = authorization.split(" ")[1]
        
        # Decode JWT token
        payload = decode_jwt(token)
        user_id = int(payload.get("sub"))
        
        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_optional_current_user(
    authorization: Optional[str] = Header(None, description="Optional Bearer token"),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Attempt to extract and validate a user from the Authorization header.

    Returns None when no header is provided or when token is invalid.
    """
    if not authorization:
        return None
    try:
        if not authorization.startswith("Bearer "):
            return None
        token = authorization.split(" ")[1]
        payload = decode_jwt(token)
        user_id = int(payload.get("sub"))
        user = await db.scalar(select(User).where(User.id == user_id))
        return user
    except Exception:
        return None

# Router setup
tournaments_router = APIRouter()

# Logger setup
logger = logging.getLogger("tournaments_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

@tournaments_router.get("/tournaments", response_model=List[TournamentResponse])
async def get_public_tournaments(
    league_id: Optional[int] = Query(None, description="Filter by league ID (optional)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all public tournaments.
    Optionally filter by league_id.
    """
    try:
        tournament_service = TournamentPostgres()
        
        if league_id:
            # Get tournaments for specific league
            tournaments = await tournament_service.get_tournaments_by_league(db, league_id)
            logger.info(f"Retrieved {len(tournaments)} public tournaments for league {league_id}")
        else:
            # Get all public tournaments
            tournaments = await tournament_service.get_public_tournaments(db)
            logger.info(f"Retrieved {len(tournaments)} public tournaments")
        
        return tournaments
        
    except Exception as e:
        logger.exception(f"Unexpected error fetching tournaments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error fetching tournaments"
        )

@tournaments_router.post("/tournaments", response_model=TournamentResponse)
async def create_tournament(
    tournament_data: TournamentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new tournament.
    Requires authentication.
    """
    try:
        logger.info(f"Creating tournament: {tournament_data.name} for user {current_user.id}")
        
        tournament_service = TournamentPostgres()
        league_service = LeaguePostgres()
        
        # Verify that the league exists
        league = await league_service.get_league_by_id(db, tournament_data.league_id)
        if not league:
            logger.error(f"League with id {tournament_data.league_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"League with id {tournament_data.league_id} not found"
            )
        
        logger.info(f"League found: {league.name}")
        
        # Create the tournament
        tournament = await tournament_service.create_tournament(
            db=db,
            name=tournament_data.name,
            creator_id=current_user.id,
            league_id=tournament_data.league_id,
            description=tournament_data.description,
            is_public=tournament_data.is_public,
            max_participants=tournament_data.max_participants
        )
        
        logger.info(f"Tournament created successfully: {tournament.name} by user {current_user.username}")
        
        return tournament
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Value error creating tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error creating tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error creating tournament"
        )

@tournaments_router.get("/tournaments/my", response_model=List[TournamentResponse])
async def get_my_tournaments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all tournaments created by the current user.
    Requires authentication.
    """
    try:
        tournament_service = TournamentPostgres()
        
        tournaments = await tournament_service.get_tournaments_by_creator(db, current_user.id)
        logger.info(f"Retrieved {len(tournaments)} tournaments for user {current_user.username}")
        
        return tournaments
        
    except Exception as e:
        logger.exception(f"Unexpected error fetching user tournaments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error fetching user tournaments"
        )

@tournaments_router.get("/tournaments/{tournament_id}", response_model=TournamentResponse)
async def get_tournament_by_id(
    tournament_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific tournament by ID.
    """
    try:
        tournament_service = TournamentPostgres()
        participation_service = TournamentParticipationPostgres()

        tournament = await tournament_service.get_tournament_by_id(db, tournament_id)
        if not tournament:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with id {tournament_id} not found"
            )

        # If tournament is public, return without auth
        if getattr(tournament, 'is_public', True):
            logger.info(f"Retrieved public tournament: {tournament.name} (id: {tournament_id})")
            return tournament

        # Private tournament: require authentication and membership
        current_user = await get_optional_current_user(db=db)
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required for private tournament")

        # Allow if creator
        if tournament.creator_id == current_user.id:
            logger.info(f"Retrieved private tournament: {tournament.name} (id: {tournament_id}) for creator {current_user.username}")
            return tournament

        is_participant = await participation_service.is_participant(db, tournament_id, current_user.id)
        if not is_participant:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: you are not a participant in this private tournament")

        logger.info(f"Retrieved private tournament: {tournament.name} (id: {tournament_id}) for user {current_user.username}")
        return tournament
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error fetching tournament {tournament_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error fetching tournament"
        )

# ===== NEW TOURNAMENT MANAGEMENT ENDPOINTS =====

@tournaments_router.post("/tournaments/{tournament_id}/join", response_model=TournamentJoinResponse)
async def join_tournament(
    tournament_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Join a tournament.
    Requires authentication.
    """
    try:
        logger.info(f"User {current_user.id} attempting to join tournament {tournament_id}")
        
        participation_service = TournamentParticipationPostgres()
        tournament_service = TournamentPostgres()
        
        # Check if tournament exists
        tournament = await tournament_service.get_tournament_by_id(db, tournament_id)
        if not tournament:
            logger.error(f"Tournament {tournament_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with id {tournament_id} not found"
            )
        
        # Check if user is already a participant
        is_participant = await participation_service.is_participant(db, tournament_id, current_user.id)
        if is_participant:
            logger.warning(f"User {current_user.id} is already a participant in tournament {tournament_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already a participant in this tournament"
            )
        
        # Join the tournament
        participation = await participation_service.join_tournament(db, tournament_id, current_user.id)
        
        logger.info(f"User {current_user.username} successfully joined tournament {tournament.name}")
        
        return TournamentJoinResponse(
            message="Joined tournament successfully",
            tournament_id=tournament_id,
            user_id=current_user.id
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Value error joining tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error joining tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error joining tournament"
        )


@tournaments_router.patch("/tournaments/{tournament_id}", response_model=TournamentResponse)
async def update_tournament(
    tournament_id: int,
    update_data: TournamentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update tournament information (only creator can update)."""
    try:
        tournament_service = TournamentPostgres()

        updated = await tournament_service.update_tournament(
            db=db,
            tournament_id=tournament_id,
            creator_id=current_user.id,
            **update_data.dict(exclude_unset=True)
        )

        return updated
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Value error updating tournament: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error updating tournament: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error updating tournament")

@tournaments_router.delete("/tournaments/{tournament_id}/leave", response_model=TournamentLeaveResponse)
async def leave_tournament(
    tournament_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Leave a tournament.
    Requires authentication.
    """
    try:
        logger.info(f"User {current_user.id} attempting to leave tournament {tournament_id}")
        
        participation_service = TournamentParticipationPostgres()
        tournament_service = TournamentPostgres()
        
        # Check if tournament exists
        tournament = await tournament_service.get_tournament_by_id(db, tournament_id)
        if not tournament:
            logger.error(f"Tournament {tournament_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with id {tournament_id} not found"
            )
        
        # Check if user is the creator
        if tournament.creator_id == current_user.id:
            logger.warning(f"Creator {current_user.id} cannot leave their own tournament {tournament_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tournament creators cannot leave their own tournament. Delete the tournament instead."
            )
        
        # Leave the tournament
        success = await participation_service.leave_tournament(db, tournament_id, current_user.id)
        
        if not success:
            logger.warning(f"User {current_user.id} was not a participant in tournament {tournament_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not a participant in this tournament"
            )
        
        logger.info(f"User {current_user.username} successfully left tournament {tournament.name}")
        
        return TournamentLeaveResponse(
            message="Left tournament successfully",
            tournament_id=tournament_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error leaving tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error leaving tournament"
        )

@tournaments_router.delete("/tournaments/{tournament_id}", response_model=TournamentDeleteResponse)
async def delete_tournament(
    tournament_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a tournament.
    Only the creator can delete their tournament.
    Requires authentication.
    """
    try:
        logger.info(f"User {current_user.id} attempting to delete tournament {tournament_id}")
        
        participation_service = TournamentParticipationPostgres()
        tournament_service = TournamentPostgres()
        
        # Check if tournament exists
        tournament = await tournament_service.get_tournament_by_id(db, tournament_id)
        if not tournament:
            logger.error(f"Tournament {tournament_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with id {tournament_id} not found"
            )
        
        # Check if user is the creator
        if tournament.creator_id != current_user.id:
            logger.warning(f"User {current_user.id} is not the creator of tournament {tournament_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the tournament creator can delete the tournament"
            )
        
        # Delete the tournament (cascade deletes participants)
        success = await participation_service.delete_tournament(db, tournament_id)
        
        if not success:
            logger.error(f"Failed to delete tournament {tournament_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete tournament"
            )
        
        logger.info(f"Tournament {tournament.name} deleted successfully by user {current_user.username}")
        
        return TournamentDeleteResponse(
            message="Tournament deleted successfully",
            id=tournament_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error deleting tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error deleting tournament"
        )

@tournaments_router.delete("/tournaments/{tournament_id}/participants/{user_id}", response_model=RemoveParticipantResponse)
async def remove_participant(
    tournament_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a participant from a tournament.
    Only the tournament creator can remove participants.
    Requires authentication.
    """
    try:
        logger.info(f"User {current_user.id} attempting to remove user {user_id} from tournament {tournament_id}")
        
        participation_service = TournamentParticipationPostgres()
        tournament_service = TournamentPostgres()
        
        # Check if tournament exists
        tournament = await tournament_service.get_tournament_by_id(db, tournament_id)
        if not tournament:
            logger.error(f"Tournament {tournament_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with id {tournament_id} not found"
            )
        
        # Check if user is the creator
        if tournament.creator_id != current_user.id:
            logger.warning(f"User {current_user.id} is not the creator of tournament {tournament_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the tournament creator can remove participants"
            )
        
        # Check if trying to remove the creator
        if user_id == current_user.id:
            logger.warning(f"Cannot remove creator {current_user.id} from tournament {tournament_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tournament creators cannot remove themselves. Delete the tournament instead."
            )
        
        # Remove the participant
        success = await participation_service.remove_participant(db, tournament_id, user_id)
        
        if not success:
            logger.warning(f"User {user_id} was not a participant in tournament {tournament_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a participant in this tournament"
            )
        
        logger.info(f"User {user_id} removed from tournament {tournament.name} by creator {current_user.username}")
        
        return RemoveParticipantResponse(
            message="User removed from tournament",
            tournament_id=tournament_id,
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error removing participant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error removing participant"
        )

@tournaments_router.get("/tournaments/{tournament_id}/participants", response_model=List[ParticipantOut])
async def get_tournament_participants(
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Get all participants of a tournament.
    Public endpoint - no authentication required.
    """
    try:
        logger.info(f"Retrieving participants for tournament {tournament_id}")
        
        participation_service = TournamentParticipationPostgres()
        tournament_service = TournamentPostgres()

        # Check if tournament exists
        tournament = await tournament_service.get_tournament_by_id(db, tournament_id)
        if not tournament:
            logger.error(f"Tournament {tournament_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with id {tournament_id} not found"
            )

        # If private tournament, require current_user membership
        if not getattr(tournament, 'is_public', True):
            if not current_user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required for private tournament participants list")
            is_participant = await participation_service.is_participant(db, tournament_id, current_user.id)
            if not is_participant and tournament.creator_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: you are not a participant in this private tournament")

        # Get participants
        participants = await participation_service.get_tournament_participants(db, tournament_id)
        
        # Convert to response format
        participant_list = []
        for participation in participants:
            participant_list.append(ParticipantOut(
                id=participation.user.id,
                username=participation.user.username,
                joined_at=participation.joined_at
            ))
        
        logger.info(f"Retrieved {len(participant_list)} participants for tournament {tournament.name}")
        
        return participant_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error fetching tournament participants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error fetching tournament participants"
        )

@tournaments_router.post("/tournaments/{tournament_id}/invite", response_model=TournamentInviteResponse)
async def invite_user_to_tournament(
    tournament_id: int,
    invite_data: TournamentInviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Invite a user to a tournament.
    Only the tournament creator can invite users.
    Requires authentication.
    """
    try:
        logger.info(f"User {current_user.id} attempting to invite user {invite_data.user_id} to tournament {tournament_id}")
        
        participation_service = TournamentParticipationPostgres()
        tournament_service = TournamentPostgres()
        
        # Check if tournament exists
        tournament = await tournament_service.get_tournament_by_id(db, tournament_id)
        if not tournament:
            logger.error(f"Tournament {tournament_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with id {tournament_id} not found"
            )
        
        # Check if user is the creator
        if tournament.creator_id != current_user.id:
            logger.warning(f"User {current_user.id} is not the creator of tournament {tournament_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the tournament creator can invite users"
            )
        
        # Check if user to invite exists
        user_to_invite = await db.scalar(select(User).where(User.id == invite_data.user_id))
        if not user_to_invite:
            logger.error(f"User {invite_data.user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {invite_data.user_id} not found"
            )
        
        # Check if user is already a participant
        is_participant = await participation_service.is_participant(db, tournament_id, invite_data.user_id)
        if is_participant:
            logger.warning(f"User {invite_data.user_id} is already a participant in tournament {tournament_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a participant in this tournament"
            )
        
        # For now, directly add the user to the tournament
        # In the future, this could create an invitation that requires acceptance
        participation = await participation_service.join_tournament(db, tournament_id, invite_data.user_id)
        
        logger.info(f"User {invite_data.user_id} invited to tournament {tournament.name} by creator {current_user.username}")
        
        return TournamentInviteResponse(
            message="User invited to tournament successfully",
            tournament_id=tournament_id,
            invited_user_id=invite_data.user_id
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Value error inviting user to tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error inviting user to tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error inviting user to tournament"
        )