from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tournament = relationship("Tournament", back_populates="participants")
    user = relationship("User", back_populates="tournament_participations")

    # Ensure unique participation per tournament
    __table_args__ = (
        UniqueConstraint('tournament_id', 'user_id', name='unique_tournament_participant'),
    )

    def to_json(self):
        return {
            "id": self.id,
            "tournament_id": self.tournament_id,
            "user_id": self.user_id,
            "joined_at": self.joined_at.isoformat(),
        }

    def __repr__(self):
        return f"<TournamentParticipant tournament_id={self.tournament_id}, user_id={self.user_id}>"
