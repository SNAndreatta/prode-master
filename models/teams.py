from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country_name = Column(Integer, ForeignKey("countries.name"), nullable=False)
    logo = Column(String(500), nullable=True)

    # Relationships
    country = relationship("Country")
    # Fixture relationships (use fixtures table instead of the removed matches model)
    home_fixtures = relationship("Fixture", primaryjoin="Team.id==Fixture.home_id", foreign_keys="Fixture.home_id")
    away_fixtures = relationship("Fixture", primaryjoin="Team.id==Fixture.away_id", foreign_keys="Fixture.away_id")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "country_name": self.country_name,
            "logo": self.logo,
        }

    def __repr__(self):
        return f"<Team {self.name} (id: {self.id})>"