import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, and_, or_, func
from sqlalchemy.exc import IntegrityError
from models.predictions import Prediction
from models.fixtures.fixture import Fixture
from models.auth.auth_models import User
from models.teams import Team
from models.rounds import Round
from models.leagues import League
from services.fixture_postgres import FixturePostgres
from models.fixtures.fixture_status import FixtureStatus
from datetime import datetime
from typing import List, Optional, Tuple, Any, cast
from sqlalchemy.orm import aliased
from services.prediction_points import PredictionPointsService

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
        penalties_home: Optional[int] = None,
        penalties_away: Optional[int] = None
    ) -> Prediction:
        """Create a new prediction for a match"""
        # Check if fixture exists and is not locked
        fixture_service = FixturePostgres()
        fixture = await fixture_service.get_fixture_by_id(db, match_id)
        if not fixture:
            raise ValueError(f"Fixture with id {match_id} not found")

        if fixture_service._is_fixture_locked(fixture):
            raise ValueError("Cannot create prediction for a fixture that has started or finished")
        
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
        try:
            await db.commit()
            await db.refresh(prediction)
        except IntegrityError as e:
            await db.rollback()
            logger.exception(f"IntegrityError while creating prediction for user {user_id} match {match_id}: {e}")
            # Likely a foreign key constraint pointing to an old 'matches' table. Surface a clearer error.
            raise ValueError(
                "Database integrity error: prediction references a non-existing match. "
                "This usually means the database foreign key still points to an old 'matches' table. "
                "Run the migration to update the constraint to reference 'fixtures(id)'."
            ) from e
        
        logger.info(f"Prediction created for user {user_id} on match {match_id}: {goals_home}-{goals_away}")
        return prediction

    async def update_prediction(
        self,
        db: AsyncSession,
        user_id: int,
        match_id: int,
        goals_home: int,
        goals_away: int,
        penalties_home: Optional[int] = None,
        penalties_away: Optional[int] = None
    ) -> Prediction:
        """Update an existing prediction"""
        # Check if fixture exists and is not locked
        fixture_service = FixturePostgres()
        fixture = await fixture_service.get_fixture_by_id(db, match_id)
        if not fixture:
            raise ValueError(f"Fixture with id {match_id} not found")

        if fixture_service._is_fixture_locked(fixture):
            raise ValueError("Cannot update prediction for a fixture that has started or finished")
        
        # Get existing prediction
        prediction = await self.get_prediction_by_user_and_match(db, user_id, match_id)
        if not prediction:
            raise ValueError("Prediction not found")
        
        # Update prediction
        setattr(prediction, 'goals_home', goals_home)
        setattr(prediction, 'goals_away', goals_away)
        setattr(prediction, 'penalties_home', penalties_home)
        setattr(prediction, 'penalties_away', penalties_away)
        setattr(prediction, 'updated_at', datetime.utcnow())

        try:
            await db.commit()
            await db.refresh(prediction)
        except IntegrityError as e:
            await db.rollback()
            logger.exception(f"IntegrityError while updating prediction for user {user_id} match {match_id}: {e}")
            raise ValueError(
                "Database integrity error: prediction references a non-existing match. "
                "This usually means the database foreign key still points to an old 'matches' table. "
                "Run the migration to update the constraint to reference 'fixtures(id)'."
            ) from e
        
        logger.info(f"Prediction updated for user {user_id} on match {match_id}: {goals_home}-{goals_away}")
        return prediction

    async def delete_prediction(
        self,
        db: AsyncSession,
        user_id: int,
        match_id: int
    ) -> bool:
        """Delete a prediction"""
        # Check if fixture exists and is not locked
        fixture_service = FixturePostgres()
        fixture = await fixture_service.get_fixture_by_id(db, match_id)
        if not fixture:
            raise ValueError(f"Fixture with id {match_id} not found")

        if fixture_service._is_fixture_locked(fixture):
            raise ValueError("Cannot delete prediction for a fixture that has started or finished")
        
        result = await db.execute(
            delete(Prediction).where(
                and_(
                    Prediction.user_id == user_id,
                    Prediction.match_id == match_id
                )
            )
        )
        await db.commit()
        
        rowcount = getattr(result, "rowcount", None)
        if rowcount and rowcount > 0:
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
            # Join with fixtures and use fixture.round/league to filter
            query = query.join(Fixture, Prediction.match_id == Fixture.id)
            if round_id:
                # Resolve round name from Round.id then filter by fixture.round
                round_obj = await db.scalar(select(Round).where(cast(Any, Round.id == round_id)))
                if round_obj:
                    query = query.where(cast(Any, Fixture.round == round_obj.name))
                else:
                    return []
            if league_id:
                query = query.where(cast(Any, Fixture.league_id == league_id))
        
        result = await db.execute(query)
        predictions = result.scalars().all()

        logger.info(f"Retrieved {len(predictions)} predictions for user {user_id}")
        return cast(List[Prediction], list(predictions))

    async def get_predictions_with_match_details(
        self,
        db: AsyncSession,
        user_id: int,
        round_id: Optional[int] = None,
        league_id: Optional[int] = None,
        match_id: Optional[int] = None
    ) -> List[Tuple[Prediction, Fixture, Team, Team, Round, League]]:
        """Get predictions with full match, team, round, and league details"""
        # Alias Team for home and away to avoid duplicate table aliasing in SQL
        HomeTeam = aliased(Team, name="home_team")
        AwayTeam = aliased(Team, name="away_team")

        # Join prediction -> fixture -> home_team -> away_team -> league -> round
        query = (
            select(Prediction, Fixture, HomeTeam, AwayTeam, Round, League)
            .join(Fixture, cast(Any, Prediction.match_id == Fixture.id))
            .join(HomeTeam, cast(Any, Fixture.home_id == HomeTeam.id))
            .join(AwayTeam, cast(Any, Fixture.away_id == AwayTeam.id))
            .join(League, cast(Any, Fixture.league_id == League.id))
            .join(Round, cast(Any, Round.league_id == League.id))  # join Round via league to keep Round available
            .where(cast(Any, Prediction.user_id == user_id))
        )

        if match_id:
            query = query.where(Prediction.match_id == match_id)
        elif round_id:
            # Resolve round name and filter by Fixture.round
            round_obj = await db.scalar(select(Round).where(cast(Any, Round.id == round_id)))
            if not round_obj:
                return []
            query = query.where(cast(Any, Fixture.round == round_obj.name))
        elif league_id:
            query = query.where(cast(Any, Round.league_id == league_id))
        
        result = await db.execute(query)
        return cast(List[Tuple[Prediction, Fixture, Team, Team, Round, League]], result.all())

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
        return cast(List[Prediction], list(predictions))

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
        return cast(List[Tuple[Prediction, User]], result.all())

    async def get_match_by_id(self, db: AsyncSession, match_id: int) -> Optional[Fixture]:
        """Get a fixture by ID (kept compatibility name)"""
        fixture_service = FixturePostgres()
        return await fixture_service.get_fixture_by_id(db, match_id)

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
        # Determine correct predictions by comparing with fixture results
        correct_result = await db.scalar(
            select(func.count(Prediction.id))
            .join(Fixture, cast(Any, Prediction.match_id == Fixture.id))
            .where(cast(Any, and_(
                cast(Any, Prediction.user_id == user_id),
                cast(Any, Fixture.status == FixtureStatus.FT),
                cast(Any, Prediction.goals_home == Fixture.home_team_score),
                cast(Any, Prediction.goals_away == Fixture.away_team_score)
            )))
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
        penalty_bonus_points: int = 3
    ) -> dict:
        """Calculate scores for all predictions of a match"""
        # Get match with results
        fixture = await self.get_match_by_id(db, match_id)
        fixture_status = getattr(fixture, 'status', None)
        if not fixture or fixture_status != FixtureStatus.FT:
            raise ValueError("Fixture not found or not finished")
        
        # Get all predictions for this match
        predictions = await self.get_match_predictions(db, match_id)
        
        # Use the dedicated scoring service. Default points passed in kept for
        # backward compatibility but the simple service below implements the
        # requested scoring: exact=3, correct winner=1, wrong=0.
        scoring_service = PredictionPointsService(exact_points=3, correct_winner_points=1)

        scores_calculated = 0
        exact_scores = 0
        correct_winners = 0
        penalty_bonuses = 0

        for prediction in predictions:
            # Extract runtime values to avoid static typing confusion
            pred_goals_home = getattr(prediction, 'goals_home')
            pred_goals_away = getattr(prediction, 'goals_away')
            pred_pens_home = getattr(prediction, 'penalties_home')
            pred_pens_away = getattr(prediction, 'penalties_away')

            fixture_goals_home = getattr(fixture, 'home_team_score')
            fixture_goals_away = getattr(fixture, 'away_team_score')
            fixture_pens_home = getattr(fixture, 'home_pens_score')
            fixture_pens_away = getattr(fixture, 'away_pens_score')

            # Score using the new service
            pts, reason = scoring_service.score_prediction(
                pred_goals_home, pred_goals_away, fixture_goals_home, fixture_goals_away
            )

            if reason == 'exact':
                exact_scores += 1
            elif reason == 'winner':
                correct_winners += 1

            score = pts

            # Penalty bonus remains: add on top of regular points
            if (pred_pens_home is not None and 
                pred_pens_away is not None and
                fixture_pens_home is not None and
                fixture_pens_away is not None):
                if (pred_pens_home == fixture_pens_home and
                    pred_pens_away == fixture_pens_away):
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

    async def calculate_and_persist_match_scores(
        self,
        db: AsyncSession,
        match_id: int,
        penalty_bonus_points: int = 3
    ) -> dict:
        """Calculate points for each prediction on a match and persist them.

        This method sets Prediction.points for each prediction and commits the
        updates. It uses the same scoring rules as PredictionPointsService
        (exact=3, winner=1, wrong=0) and adds penalty bonus on top.
        """
        # Get match with results
        fixture = await self.get_match_by_id(db, match_id)
        fixture_status = getattr(fixture, 'status', None)
        if not fixture or fixture_status != FixtureStatus.FT:
            raise ValueError("Fixture not found or not finished")

        predictions = await self.get_match_predictions(db, match_id)

        scoring_service = PredictionPointsService(exact_points=3, correct_winner_points=1)

        updated = 0
        for prediction in predictions:
            pred_goals_home = getattr(prediction, 'goals_home')
            pred_goals_away = getattr(prediction, 'goals_away')
            pred_pens_home = getattr(prediction, 'penalties_home')
            pred_pens_away = getattr(prediction, 'penalties_away')

            fixture_goals_home = getattr(fixture, 'home_team_score')
            fixture_goals_away = getattr(fixture, 'away_team_score')
            fixture_pens_home = getattr(fixture, 'home_pens_score')
            fixture_pens_away = getattr(fixture, 'away_pens_score')

            pts, _reason = scoring_service.score_prediction(
                pred_goals_home, pred_goals_away, fixture_goals_home, fixture_goals_away
            )

            # Penalty bonus
            if (pred_pens_home is not None and pred_pens_away is not None and
                fixture_pens_home is not None and fixture_pens_away is not None):
                if (pred_pens_home == fixture_pens_home and pred_pens_away == fixture_pens_away):
                    pts += penalty_bonus_points

            # Persist
            prediction.points = pts
            prediction.updated_at = datetime.utcnow()
            updated += 1

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        return {
            "match_id": match_id,
            "total_predictions": len(predictions),
            "scores_calculated": updated
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
                cast(Any, and_(
                    cast(Any, TournamentParticipant.tournament_id == tournament_id),
                    cast(Any, Prediction.match_id == match_id)
                ))
            )
        )
        return cast(List[Tuple[Prediction, User]], result.all())
