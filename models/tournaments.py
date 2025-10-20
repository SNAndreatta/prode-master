from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Tournament(Base):
    """Tournament ORM class

    Args:
        id (int): The tournament's unique identifier.
        name (str): The tournament's name.
        description (str): Optional description of the tournament.
        is_public (bool): Whether the tournament is public or private.
        creator_id (int): The ID of the user who created the tournament.
        league_id (int): The ID of the league this tournament is associated with.
        max_participants (int): Maximum number of participants allowed.
        created_at (datetime): When the tournament was created.
        updated_at (datetime): When the tournament was last updated.
    """

    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    max_participants = Column(Integer, default=100, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="created_tournaments")
    league = relationship("League")
    participants = relationship("TournamentParticipant", back_populates="tournament", cascade="all, delete-orphan")

    def __init__(self, name: str, creator_id: int, league_id: int, description: str = None, 
                 is_public: bool = True, max_participants: int = 100):
        self.name = name
        self.description = description
        self.is_public = is_public
        self.creator_id = creator_id
        self.league_id = league_id
        self.max_participants = max_participants

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_public": self.is_public,
            "creator_id": self.creator_id,
            "league_id": self.league_id,
            "max_participants": self.max_participants,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Tournament {self.name} (id: {self.id}, public: {self.is_public})>"
