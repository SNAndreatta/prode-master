from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List

# Request schemas
class PredictionCreate(BaseModel):
    match_id: int = Field(..., description="ID of the match to predict")
    goals_home: int = Field(..., ge=0, description="Predicted goals for home team")
    goals_away: int = Field(..., ge=0, description="Predicted goals for away team")
    penalties_home: Optional[int] = Field(None, ge=0, description="Predicted penalties for home team (optional)")
    penalties_away: Optional[int] = Field(None, ge=0, description="Predicted penalties for away team (optional)")

    @validator('penalties_home', 'penalties_away')
    def validate_penalties(cls, v, values):
        if v is not None and v < 0:
            raise ValueError('Penalties must be non-negative')
        return v

class PredictionUpdate(BaseModel):
    goals_home: int = Field(..., ge=0, description="Predicted goals for home team")
    goals_away: int = Field(..., ge=0, description="Predicted goals for away team")
    penalties_home: Optional[int] = Field(None, ge=0, description="Predicted penalties for home team (optional)")
    penalties_away: Optional[int] = Field(None, ge=0, description="Predicted penalties for away team (optional)")

# Response schemas
class PredictionResponse(BaseModel):
    id: int
    user_id: int
    match_id: int
    goals_home: int
    goals_away: int
    penalties_home: Optional[int]
    penalties_away: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PredictionWithMatch(BaseModel):
    id: int
    user_id: int
    match_id: int
    goals_home: int
    goals_away: int
    penalties_home: Optional[int]
    penalties_away: Optional[int]
    created_at: datetime
    updated_at: datetime
    match: 'MatchResponse'

    class Config:
        from_attributes = True

class MatchResponse(BaseModel):
    id: int
    round_id: int
    home_team_id: int
    away_team_id: int
    start_time: datetime
    finished: bool
    result_goals_home: Optional[int]
    result_goals_away: Optional[int]
    result_penalties_home: Optional[int]
    result_penalties_away: Optional[int]

    class Config:
        from_attributes = True

class PredictionStats(BaseModel):
    total_predictions: int
    correct_predictions: int
    accuracy_percentage: float
    average_goals_predicted: float
    most_common_outcome: str

class UserPredictionSummary(BaseModel):
    user_id: int
    username: str
    total_predictions: int
    correct_predictions: int
    accuracy_percentage: float

# Admin schemas
class AdminPredictionResponse(BaseModel):
    id: int
    user_id: int
    username: str
    match_id: int
    goals_home: int
    goals_away: int
    penalties_home: Optional[int]
    penalties_away: Optional[int]
    created_at: datetime
    updated_at: datetime
    match: MatchResponse

    class Config:
        from_attributes = True

class ScoreCalculationRequest(BaseModel):
    match_id: int = Field(..., description="ID of the match to calculate scores for")
    exact_score_points: int = Field(10, description="Points for exact score prediction")
    correct_winner_points: int = Field(5, description="Points for correct winner prediction")
    penalty_bonus_points: int = Field(3, description="Bonus points for correct penalty prediction")

class ScoreCalculationResponse(BaseModel):
    match_id: int
    total_predictions: int
    scores_calculated: int
    exact_scores: int
    correct_winners: int
    penalty_bonuses: int
