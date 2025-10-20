from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)  # nuevo campo
    hashed_password = Column(String, nullable=False)
    
    # Relationships
    created_tournaments = relationship("Tournament", back_populates="creator")
    tournament_participations = relationship("TournamentParticipant", back_populates="user")
    predictions = relationship("Prediction", back_populates="user")
    
class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    refresh_token = Column(String, unique=True, nullable=False)
    revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    user_agent = Column(String, nullable=True)  # nuevo campo para UserAgent

    user = relationship("User")

    
