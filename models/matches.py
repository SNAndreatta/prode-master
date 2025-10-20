from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    finished = Column(Boolean, default=False, nullable=False)
    
    # Actual results (filled after match completion)
    result_goals_home = Column(Integer, nullable=True)
    result_goals_away = Column(Integer, nullable=True)
    result_penalties_home = Column(Integer, nullable=True)
    result_penalties_away = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    round = relationship("Round", back_populates="matches")
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
    predictions = relationship("Prediction", back_populates="match", cascade="all, delete-orphan")

    def to_json(self):
        return {
            "id": self.id,
            "round_id": self.round_id,
            "home_team_id": self.home_team_id,
            "away_team_id": self.away_team_id,
            "start_time": self.start_time.isoformat(),
            "finished": self.finished,
            "result_goals_home": self.result_goals_home,
            "result_goals_away": self.result_goals_away,
            "result_penalties_home": self.result_penalties_home,
            "result_penalties_away": self.result_penalties_away,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def is_locked(self):
        """Check if predictions are locked (match started or finished)"""
        return self.finished or datetime.utcnow() >= self.start_time

    def __repr__(self):
        return f"<Match {self.home_team_id} vs {self.away_team_id} (id: {self.id})>"
