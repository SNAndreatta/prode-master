from sqlalchemy import Column, String, Text, ForeignKey, Integer
from database import Base
from models.countries import Country
class League(Base):
    """League ORM class

    Args:
        id (int): The league's unique identifier.
        name (str): The league's full name (e.g., "Premier League").
        country_name (str): The name of the country the league is from (e.g., "England").
        logo (str): URL or path to the league's logo image.
    """

    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, nullable=False)

    name = Column(String(100), nullable=True, unique=False)
    country_name = Column(String(100), ForeignKey("countries.name"), nullable=False)
    logo = Column(Text, nullable=True)
    season = Column(Integer, nullable=False)

    def __init__(self, id: int, name: str, country_name: str, season: int, logo: str = None):
        self.id = id
        self.name = name
        self.country_name = country_name
        self.logo = logo
        self.season = season

    def __len__(self):
        return 1

    def __iter__(self):
        return iter([self])

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country_name,
            "logo": self.logo,
            "season": self.season,
        }

    def __repr__(self):
        return f"<League {self.name} year {self.season} (from: {self.country_name} // id: {self.id})>"
