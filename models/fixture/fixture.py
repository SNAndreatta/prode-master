from sqlalchemy import Column, String, ForeignKey, Integer, DateTime
from database import Base

class Fixture(Base):
    """Fixture ORM class

    Args:
        id (int): The fixture's unique identifier.
        league_id (int): The fixture's league ID.
        home_id (int): The ID of the first team in the fixture.
        away_id (int): The ID of the second team in the fixture.
        date (datetime): The date and time of the fixture.
        home_team_score (int): The score of the home team.
        away_team_score (int): The score of the away team.
        home_pens_score (int): The number of penalties scored by the home team.
        away_pens_score (int): The number of penalties scored by the away team.
    """

    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True, nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    home_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    date = Column(DateTime, nullable=True)
    home_team_score = Column(Integer, nullable=True)
    away_team_score = Column(Integer, nullable=True)
    home_pens_score = Column(Integer, nullable=True)
    away_pens_score = Column(Integer, nullable=True)

    def __init__(self,id: int, league_id: int, home_id: int, away_id: int, date: String, home_team_score: int, away_team_score: int, home_pens_score: int,away_pens_score: int,):
        self.id = id
        self.league_id = league_id
        self.home_id = home_id
        self.away_id = away_id
        self.date = date
        self.home_team_score = home_team_score
        self.away_team_score = away_team_score
        self.home_pens_score = home_pens_score
        self.away_pens_score = away_pens_score

    def to_json(self):
        return {
            "id": self.id,
            "league_id": self.league_id,
            "home_id": self.home_id,
            "away_id": self.away_id,
            "date": self.date,
            "home_team_score": self.home_team_score,
            "away_team_score": self.away_team_score,
            "home_pens_score": self.home_pens_score,
            "away_pens_score": self.away_pens_score,
        }

    def __repr__(self):
        return f"<Fixture {self.league_id} home: {self.home_id} away: {self.away_id} date: {self.date} home_score: {self.home_team_score} away_score: {self.away_team_score} home_pens_score: {self.home_pens_score} away_pens_score: {self.away_pens_score}>"
