from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from api.db.database import Base


class Hall(Base):
    __tablename__ = "halls"

    id = Column(Integer, primary_key=True, index=True)
    hall_name = Column(String, unique=True, nullable=False)
    no_beds = Column(Integer, nullable=False)
    no_allocated_beds = Column(Integer, default=0, nullable=False)
    no_floors = Column(Integer, nullable=False)

    residents = relationship("User", back_populates="hall")
    categories = relationship("Category", back_populates="hall")
