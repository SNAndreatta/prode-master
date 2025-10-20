from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship
from database import Base
class Round(Base):
    """Round ORM class

    Args:
        id (int): The round's unique identifier.
        name (str): The round's full name (e.g., "Regular Season").
        league_id (int): The unique identifier of the league the round belongs to.
        season (int): The season the round belongs to.
    """

    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)

    name = Column(String(100), nullable=True, unique=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    season = Column(Integer, nullable=False)

    # Relationships
    league = relationship("League")
    matches = relationship("Match", back_populates="round")

    def __init__(self, id: int, name: str, league_id: int, season: int):
        self.id = id
        self.name = name
        self.league_id = league_id
        self.season = season

    def __len__(self):
        return 1

    def __iter__(self):
        return iter([self])

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "league": self.league_id
        }

    def __repr__(self):
        return f"<Round {self.name} year {self.season} (from: {self.league_id} // id: {self.id})>"
