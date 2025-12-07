from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from api.db.database import Base


class Hall(Base):
    __tablename__ = "halls"

    id = Column(Integer, primary_key=True, index=True)
    hall_name = Column(String, unique=True, nullable=False)
    no_beds = Column(Integer, nullable=False)
    no_floors = Column(Integer, nullable=False)
    gender = Column(Enum("male", "female", name="gender_enum"), nullable=False)

    residents = relationship("User", back_populates="hall")
    floors = relationship("HallFloors", back_populates="hall_relationship")