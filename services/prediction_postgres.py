import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, and_, or_, func
from models.predictions import Prediction
from models.matches import Match
from models.auth.auth_models import User
from models.teams import Team
from models.rounds import Round
from models.leagues import League
from datetime import datetime
from typing import List, Optional, Tuple

logger = logging.getLogger("prediction_service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

class PredictionPostgres:
    async def create_prediction(
        self,
        db: AsyncSession,
        user_id: int,
        match_id: int,
        goals_home: int,
        goals_away: int,
        penalties_home: int = None,
        penalties_away: int = None
    ) -> Prediction:
        """Create a new prediction for a match"""
        # Check if match exists and is not locked
        match = await self.get_match_by_id(db, match_id)
        if not match:
            raise ValueError(f"Match with id {match_id} not found")
        
        if match.is_locked():
            raise ValueError("Cannot create prediction for a match that has started or finished")
        
        # Check if prediction already exists
        existing_prediction = await self.get_prediction_by_user_and_match(db, user_id, match_id)
        if existing_prediction:
            raise ValueError("Prediction already exists for this match")
        
        prediction = Prediction(
            user_id=user_id,
            match_id=match_id,
            goals_home=goals_home,
            goals_away=goals_away,
            penalties_home=penalties_home,
            penalties_away=penalties_away
        )
        
        db.add(prediction)
        await db.commit()
        await db.refresh(prediction)
        
        logger.info(f"Prediction created for user {user_id} on match {match_id}: {goals_home}-{goals_away}")
        return prediction

    async def update_prediction(
        self,
        db: AsyncSession,
        user_id: int,
        match_id: int,
        goals_home: int,
        goals_away: int,
        penalties_home: int = None,
        penalties_away: int = None
    ) -> Prediction:
        """Update an existing prediction"""
        # Check if match exists and is not locked
        match = await self.get_match_by_id(db, match_id)
        if not match:
            raise ValueError(f"Match with id {match_id} not found")
        
        if match.is_locked():
            raise ValueError("Cannot update prediction for a match that has started or finished")
        
        # Get existing prediction
        prediction = await self.get_prediction_by_user_and_match(db, user_id, match_id)
        if not prediction:
            raise ValueError("Prediction not found")
        
        # Update prediction
        prediction.goals_home = goals_home
        prediction.goals_away = goals_away
        prediction.penalties_home = penalties_home
        prediction.penalties_away = penalties_away
        prediction.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(prediction)
        
        logger.info(f"Prediction updated for user {user_id} on match {match_id}: {goals_home}-{goals_away}")
        return prediction

    async def delete_prediction(
        self,
        db: AsyncSession,
        user_id: int,
        match_id: int
    ) -> bool:
        """Delete a prediction"""
        # Check if match exists and is not locked
        match = await self.get_match_by_id(db, match_id)
        if not match:
            raise ValueError(f"Match with id {match_id} not found")
        
        if match.is_locked():
            raise ValueError("Cannot delete prediction for a match that has started or finished")
        
        result = await db.execute(
            delete(Prediction).where(
                and_(
                    Prediction.user_id == user_id,
                    Prediction.match_id == match_id
                )
            )
        )
        await db.commit()
        
        if result.rowcount > 0:
            logger.info(f"Prediction deleted for user {user_id} on match {match_id}")
            return True
        else:
            logger.warning(f"No prediction found for user {user_id} on match {match_id}")
            return False

    async def get_prediction_by_user_and_match(
        self,
        db: AsyncSession,
        user_id: int,
        match_id: int
    ) -> Optional[Prediction]:
        """Get a specific prediction by user and match"""
        result = await db.scalar(
            select(Prediction).where(
                and_(
                    Prediction.user_id == user_id,
                    Prediction.match_id == match_id
                )
            )
        )
        return result

    async def get_user_predictions(
        self,
        db: AsyncSession,
        user_id: int,
        round_id: Optional[int] = None,
        league_id: Optional[int] = None,
        match_id: Optional[int] = None
    ) -> List[Prediction]:
        """Get all predictions for a user with optional filters"""
        query = select(Prediction).where(Prediction.user_id == user_id)
        
        if match_id:
            query = query.where(Prediction.match_id == match_id)
        elif round_id or league_id:
            # Join with matches and rounds to filter
            query = query.join(Match).join(Round)
            if round_id:
                query = query.where(Round.id == round_id)
            if league_id:
                query = query.where(Round.league_id == league_id)
        
        result = await db.execute(query)
        predictions = result.scalars().all()
        
        logger.info(f"Retrieved {len(predictions)} predictions for user {user_id}")
        return predictions

    async def get_predictions_with_match_details(
        self,
        db: AsyncSession,
        user_id: int,
        round_id: Optional[int] = None,
        league_id: Optional[int] = None,
        match_id: Optional[int] = None
    ) -> List[Tuple[Prediction, Match, Team, Team, Round, League]]:
        """Get predictions with full match, team, round, and league details"""
        query = (
            select(Prediction, Match, Team, Team, Round, League)
            .join(Match, Prediction.match_id == Match.id)
            .join(Team, Match.home_team_id == Team.id)
            .join(Team, Match.away_team_id == Team.id)
            .join(Round, Match.round_id == Round.id)
            .join(League, Round.league_id == League.id)
            .where(Prediction.user_id == user_id)
        )
        
        if match_id:
            query = query.where(Prediction.match_id == match_id)
        elif round_id:
            query = query.where(Round.id == round_id)
        elif league_id:
            query = query.where(Round.league_id == league_id)
        
        result = await db.execute(query)
        return result.all()

    async def get_match_predictions(
        self,
        db: AsyncSession,
        match_id: int
    ) -> List[Prediction]:
        """Get all predictions for a specific match"""
        result = await db.execute(
            select(Prediction).where(Prediction.match_id == match_id)
        )
        predictions = result.scalars().all()
        
        logger.info(f"Retrieved {len(predictions)} predictions for match {match_id}")
        return predictions

    async def get_match_predictions_with_users(
        self,
        db: AsyncSession,
        match_id: int
    ) -> List[Tuple[Prediction, User]]:
        """Get all predictions for a match with user details"""
        result = await db.execute(
            select(Prediction, User)
            .join(User, Prediction.user_id == User.id)
            .where(Prediction.match_id == match_id)
        )
        return result.all()

    async def get_match_by_id(self, db: AsyncSession, match_id: int) -> Optional[Match]:
        """Get a match by ID"""
        result = await db.scalar(select(Match).where(Match.id == match_id))
        return result

    async def get_user_prediction_stats(
        self,
        db: AsyncSession,
        user_id: int
    ) -> dict:
        """Get prediction statistics for a user"""
        # Get total predictions
        total_result = await db.scalar(
            select(func.count(Prediction.id)).where(Prediction.user_id == user_id)
        )
        total_predictions = total_result or 0
        
        # Get correct predictions (exact score)
        correct_result = await db.scalar(
            select(func.count(Prediction.id))
            .join(Match, Prediction.match_id == Match.id)
            .where(
                and_(
                    Prediction.user_id == user_id,
                    Match.finished == True,
                    Prediction.goals_home == Match.result_goals_home,
                    Prediction.goals_away == Match.result_goals_away
                )
            )
        )
        correct_predictions = correct_result or 0
        
        # Get average goals predicted
        avg_result = await db.scalar(
            select(func.avg(Prediction.goals_home + Prediction.goals_away))
            .where(Prediction.user_id == user_id)
        )
        average_goals = float(avg_result) if avg_result else 0.0
        
        # Calculate accuracy
        accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0.0
        
        return {
            "total_predictions": total_predictions,
            "correct_predictions": correct_predictions,
            "accuracy_percentage": round(accuracy, 2),
            "average_goals_predicted": round(average_goals, 2)
        }

    async def calculate_match_scores(
        self,
        db: AsyncSession,
        match_id: int,
        exact_score_points: int = 10,
        correct_winner_points: int = 5,
        penalty_bonus_points: int = 3
    ) -> dict:
        """Calculate scores for all predictions of a match"""
        # Get match with results
        match = await self.get_match_by_id(db, match_id)
        if not match or not match.finished:
            raise ValueError("Match not found or not finished")
        
        # Get all predictions for this match
        predictions = await self.get_match_predictions(db, match_id)
        
        scores_calculated = 0
        exact_scores = 0
        correct_winners = 0
        penalty_bonuses = 0
        
        for prediction in predictions:
            score = 0
            
            # Check exact score
            if (prediction.goals_home == match.result_goals_home and 
                prediction.goals_away == match.result_goals_away):
                score += exact_score_points
                exact_scores += 1
            else:
                # Check correct winner
                prediction_winner = self._get_winner(prediction.goals_home, prediction.goals_away)
                actual_winner = self._get_winner(match.result_goals_home, match.result_goals_away)
                
                if prediction_winner == actual_winner:
                    score += correct_winner_points
                    correct_winners += 1
            
            # Check penalty bonus
            if (prediction.penalties_home is not None and 
                prediction.penalties_away is not None and
                match.result_penalties_home is not None and
                match.result_penalties_away is not None):
                
                if (prediction.penalties_home == match.result_penalties_home and
                    prediction.penalties_away == match.result_penalties_away):
                    score += penalty_bonus_points
                    penalty_bonuses += 1
            
            scores_calculated += 1
            logger.info(f"User {prediction.user_id} scored {score} points for match {match_id}")
        
        return {
            "match_id": match_id,
            "total_predictions": len(predictions),
            "scores_calculated": scores_calculated,
            "exact_scores": exact_scores,
            "correct_winners": correct_winners,
            "penalty_bonuses": penalty_bonuses
        }

    def _get_winner(self, goals_home: int, goals_away: int) -> str:
        """Determine winner based on goals"""
        if goals_home > goals_away:
            return "home"
        elif goals_away > goals_home:
            return "away"
        else:
            return "draw"

    async def get_tournament_participants_predictions(
        self,
        db: AsyncSession,
        tournament_id: int,
        match_id: int
    ) -> List[Tuple[Prediction, User]]:
        """Get predictions for a specific match from tournament participants"""
        from models.tournament_participants import TournamentParticipant
        
        result = await db.execute(
            select(Prediction, User)
            .join(User, Prediction.user_id == User.id)
            .join(TournamentParticipant, User.id == TournamentParticipant.user_id)
            .where(
                and_(
                    TournamentParticipant.tournament_id == tournament_id,
                    Prediction.match_id == match_id
                )
            )
        )
        return result.all()
