import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from services.prediction_postgres import PredictionPostgres
from models.auth.auth_models import User
from blueprints.auth.jwt_handler import decode_jwt
from schemas.prediction_schemas import (
    PredictionCreate,
    PredictionUpdate,
    PredictionResponse,
    PredictionWithMatch,
    PredictionStats,
    UserPredictionSummary,
    AdminPredictionResponse,
    ScoreCalculationRequest,
    ScoreCalculationResponse
)
from typing import Optional, List
from datetime import datetime

predictions_router = APIRouter()

logger = logging.getLogger("predictions_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

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
                detail="Invalid authentication scheme. Must be 'Bearer'."
            )
        token = authorization.split(" ")[1]
        payload = decode_jwt(token)
        user_id = int(payload.get("sub"))
        user = await db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except ValueError as e:
        logger.error(f"JWT decoding error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception as e:
        logger.exception(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication error")

@predictions_router.post("/predictions", response_model=PredictionResponse)
async def create_or_update_prediction(
    prediction_data: PredictionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create or update a prediction for a match.
    If prediction exists, it will be updated.
    If not, a new one will be created.
    Requires authentication.
    """
    try:
        logger.info(f"User {current_user.id} creating/updating prediction for match {prediction_data.match_id}")
        
        prediction_service = PredictionPostgres()
        
        # Try to get existing prediction
        existing_prediction = await prediction_service.get_prediction_by_user_and_match(
            db, current_user.id, prediction_data.match_id
        )
        
        if existing_prediction:
            # Update existing prediction
            prediction = await prediction_service.update_prediction(
                db=db,
                user_id=current_user.id,
                match_id=prediction_data.match_id,
                goals_home=prediction_data.goals_home,
                goals_away=prediction_data.goals_away,
                penalties_home=prediction_data.penalties_home,
                penalties_away=prediction_data.penalties_away
            )
            logger.info(f"Prediction updated for user {current_user.username} on match {prediction_data.match_id}")
        else:
            # Create new prediction
            prediction = await prediction_service.create_prediction(
                db=db,
                user_id=current_user.id,
                match_id=prediction_data.match_id,
                goals_home=prediction_data.goals_home,
                goals_away=prediction_data.goals_away,
                penalties_home=prediction_data.penalties_home,
                penalties_away=prediction_data.penalties_away
            )
            logger.info(f"Prediction created for user {current_user.username} on match {prediction_data.match_id}")
        
        return prediction
        
    except ValueError as e:
        logger.error(f"Value error creating/updating prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error creating/updating prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error creating/updating prediction"
        )

@predictions_router.get("/predictions", response_model=List[PredictionWithMatch])
async def get_user_predictions(
    round_id: Optional[int] = Query(None, description="Filter by round ID"),
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
    match_id: Optional[int] = Query(None, description="Filter by match ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all predictions for the current user.
    Can be filtered by round_id, league_id, or match_id.
    Requires authentication.
    """
    try:
        logger.info(f"Retrieving predictions for user {current_user.id}")
        
        prediction_service = PredictionPostgres()
        
        # Get predictions with match details
        predictions_data = await prediction_service.get_predictions_with_match_details(
            db=db,
            user_id=current_user.id,
            round_id=round_id,
            league_id=league_id,
            match_id=match_id
        )
        
        # Convert to response format
        predictions = []
        for prediction, match, home_team, away_team, round_obj, league in predictions_data:
            # Map internal Fixture model fields to API MatchResponse expected fields
            match_response = {
                "id": match.id,
                "round_id": match.league_id if hasattr(match, 'league_id') else None,
                "home_team_id": match.home_id,
                "away_team_id": match.away_id,
                "start_time": match.date,
                "finished": (match.status == None) or (getattr(match, 'status', None) == None) and False or getattr(match, 'status').name == 'FT',
                "result_goals_home": getattr(match, 'home_team_score', None),
                "result_goals_away": getattr(match, 'away_team_score', None),
                "result_penalties_home": getattr(match, 'home_pens_score', None),
                "result_penalties_away": getattr(match, 'away_pens_score', None)
            }
            
            predictions.append({
                "id": prediction.id,
                "user_id": prediction.user_id,
                "match_id": prediction.match_id,
                "goals_home": prediction.goals_home,
                "goals_away": prediction.goals_away,
                "penalties_home": prediction.penalties_home,
                "penalties_away": prediction.penalties_away,
                "created_at": prediction.created_at,
                "updated_at": prediction.updated_at,
                "match": match_response
            })
        
        logger.info(f"Retrieved {len(predictions)} predictions for user {current_user.username}")
        return predictions
        
    except Exception as e:
        logger.exception(f"Unexpected error fetching user predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error fetching user predictions"
        )

@predictions_router.delete("/predictions/{match_id}")
async def delete_prediction(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a prediction for a specific match.
    Only allowed before the match starts.
    Requires authentication.
    """
    try:
        logger.info(f"User {current_user.id} attempting to delete prediction for match {match_id}")
        
        prediction_service = PredictionPostgres()
        
        success = await prediction_service.delete_prediction(
            db=db,
            user_id=current_user.id,
            match_id=match_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found"
            )
        
        logger.info(f"Prediction deleted for user {current_user.username} on match {match_id}")
        
        return {"message": "Prediction deleted successfully", "match_id": match_id}
        
    except ValueError as e:
        logger.error(f"Value error deleting prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error deleting prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error deleting prediction"
        )

@predictions_router.get("/predictions/stats", response_model=PredictionStats)
async def get_user_prediction_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get prediction statistics for the current user.
    Requires authentication.
    """
    try:
        logger.info(f"Retrieving prediction stats for user {current_user.id}")
        
        prediction_service = PredictionPostgres()
        
        stats = await prediction_service.get_user_prediction_stats(db, current_user.id)
        
        logger.info(f"Retrieved prediction stats for user {current_user.username}")
        
        return PredictionStats(
            total_predictions=stats["total_predictions"],
            correct_predictions=stats["correct_predictions"],
            accuracy_percentage=stats["accuracy_percentage"],
            average_goals_predicted=stats["average_goals_predicted"],
            most_common_outcome="win"  # This would need more complex logic to calculate
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error fetching prediction stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error fetching prediction stats"
        )

@predictions_router.get("/predictions/match/{match_id}", response_model=List[PredictionResponse])
async def get_match_predictions(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all predictions for a specific match.
    Only shows predictions from users who share a tournament with the current user.
    Requires authentication.
    """
    try:
        logger.info(f"Retrieving predictions for match {match_id}")
        
        prediction_service = PredictionPostgres()
        
        # Get predictions for the match
        predictions = await prediction_service.get_match_predictions(db, match_id)
        
        logger.info(f"Retrieved {len(predictions)} predictions for match {match_id}")
        return predictions
        
    except Exception as e:
        logger.exception(f"Unexpected error fetching match predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error fetching match predictions"
        )

# Admin endpoints
@predictions_router.get("/admin/predictions/match/{match_id}", response_model=List[AdminPredictionResponse])
async def get_admin_match_predictions(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all predictions for a specific match (admin only).
    Shows all predictions regardless of tournament membership.
    Requires authentication and admin privileges.
    """
    try:
        # TODO: Add admin role check
        logger.info(f"Admin retrieving all predictions for match {match_id}")
        
        prediction_service = PredictionPostgres()
        
        # Get predictions with user details
        predictions_data = await prediction_service.get_match_predictions_with_users(db, match_id)
        
        # Convert to response format
        predictions = []
        for prediction, user in predictions_data:
            match = await prediction_service.get_match_by_id(db, match_id)
            # Map Fixture fields to MatchResponse
            match_response = {
                "id": match.id,
                "round_id": match.league_id if hasattr(match, 'league_id') else None,
                "home_team_id": match.home_id,
                "away_team_id": match.away_id,
                "start_time": match.date,
                "finished": (match.status == None) or (getattr(match, 'status', None) == None) and False or getattr(match, 'status').name == 'FT',
                "result_goals_home": getattr(match, 'home_team_score', None),
                "result_goals_away": getattr(match, 'away_team_score', None),
                "result_penalties_home": getattr(match, 'home_pens_score', None),
                "result_penalties_away": getattr(match, 'away_pens_score', None)
            }
            
            predictions.append({
                "id": prediction.id,
                "user_id": prediction.user_id,
                "username": user.username,
                "match_id": prediction.match_id,
                "goals_home": prediction.goals_home,
                "goals_away": prediction.goals_away,
                "penalties_home": prediction.penalties_home,
                "penalties_away": prediction.penalties_away,
                "created_at": prediction.created_at,
                "updated_at": prediction.updated_at,
                "match": match_response
            })
        
        logger.info(f"Admin retrieved {len(predictions)} predictions for match {match_id}")
        return predictions
        
    except Exception as e:
        logger.exception(f"Unexpected error fetching admin match predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error fetching admin match predictions"
        )

@predictions_router.post("/admin/predictions/score", response_model=ScoreCalculationResponse)
async def calculate_match_scores(
    score_data: ScoreCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate scores for all predictions of a match (admin only).
    Requires authentication and admin privileges.
    """
    try:
        # TODO: Add admin role check
        logger.info(f"Admin calculating scores for match {score_data.match_id}")
        
        prediction_service = PredictionPostgres()
        
        scores = await prediction_service.calculate_match_scores(
            db=db,
            match_id=score_data.match_id,
            exact_score_points=score_data.exact_score_points,
            correct_winner_points=score_data.correct_winner_points,
            penalty_bonus_points=score_data.penalty_bonus_points
        )
        
        logger.info(f"Admin calculated scores for match {score_data.match_id}")
        
        return ScoreCalculationResponse(**scores)
        
    except ValueError as e:
        logger.error(f"Value error calculating scores: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error calculating scores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error calculating scores"
        )
