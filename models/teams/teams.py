from sqlalchemy import Column, String, Text, Integer, ForeignKey
from database import Base

class Team(Base):
    """Team ORM class

    Args:
        id (int): The team's unique identifier.
        name (str): The team's full name (e.g., "Manchester United").
        logo (str): URL or path to the team's logo image.
        country_name (str): The name of the country the team is from (e.g., "England").
    """

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(100), nullable=False)
    logo = Column(Text, nullable=True)
    country_name = Column(String(100), ForeignKey("countries.name"), nullable=True)

    def __init__(self, id: int, name: str, logo: str = None, country_name: str = None):
        self.id = id
        self.name = name
        self.logo = logo
        self.country_name = country_name

    def __repr__(self):
        return f"<Team {self.name} (from: {self.country_name} // id: {self.id})>"
