from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Response schemas for tournament management
class TournamentJoinResponse(BaseModel):
    message: str
    tournament_id: int
    user_id: int

class TournamentLeaveResponse(BaseModel):
    message: str
    tournament_id: int

class TournamentDeleteResponse(BaseModel):
    message: str
    id: int

class RemoveParticipantResponse(BaseModel):
    message: str
    tournament_id: int
    user_id: int

class ParticipantOut(BaseModel):
    id: int
    username: str
    joined_at: datetime
    
    class Config:
        from_attributes = True

class TournamentInviteRequest(BaseModel):
    user_id: int

class TournamentVisibilityRequest(BaseModel):
    is_public: bool

class TournamentInviteResponse(BaseModel):
    message: str
    tournament_id: int
    invited_user_id: int

class TournamentVisibilityResponse(BaseModel):
    message: str
    tournament_id: int
    is_public: bool
