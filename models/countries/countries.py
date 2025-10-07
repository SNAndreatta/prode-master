import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Text
from database import Base
from sqlalchemy.orm import relationship


class Country(Base):
    """Country ORM class

    Args:
        name (str): The country's full name (e.g., "France").
        code (str): ISO 2- or 3-letter country code (e.g., "FR" or "FRA").
        flag (str): URL or path to the country's flag image.
    """

    __tablename__ = "countries"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(10), nullable=False, unique=True)
    flag = Column(Text, nullable=True)

    # Example: relationship with City or User, if applicable
    # cities = relationship("City", back_populates="country")

    def __repr__(self):
        return f"<Country {self.name} ({self.code})>"
