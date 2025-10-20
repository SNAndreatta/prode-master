from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    goals_home = Column(Integer, nullable=False)
    goals_away = Column(Integer, nullable=False)
    penalties_home = Column(Integer, nullable=True)
    penalties_away = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")

    # Ensure unique prediction per user per match
    __table_args__ = (
        UniqueConstraint('user_id', 'match_id', name='unique_user_match_prediction'),
    )

    def to_json(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "match_id": self.match_id,
            "goals_home": self.goals_home,
            "goals_away": self.goals_away,
            "penalties_home": self.penalties_home,
            "penalties_away": self.penalties_away,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Prediction user_id={self.user_id}, match_id={self.match_id}, score={self.goals_home}-{self.goals_away}>"
