from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    logo_url = Column(String(500), nullable=True)

    # Relationships
    country = relationship("Country")
    league = relationship("League")
    home_matches = relationship("Match", foreign_keys="Match.home_team_id")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "country_id": self.country_id,
            "league_id": self.league_id,
            "logo_url": self.logo_url,
        }

    def __repr__(self):
        return f"<Team {self.name} (id: {self.id})>"