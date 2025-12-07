from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from api.db.database import Base


class HallFloors(Base):
    __tablename__ = "hall_floors"
    
    floor_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    hall_id = Column(ForeignKey("halls.id"), nullable=False)
    floor_no = Column(Integer, nullable=False)
    age_range = Column(Enum("10-17", "18-25", "26-35", "36-45", "45-55", "56-65", "66-70", "71+", name="age_range_enum"), nullable=True)

    no_beds = Column(Integer, nullable=True, default=0)
    last_assigned_bed = Column(Integer, nullable=True, default=0)
    status = Column(Enum("full", "not-full", name="floor_status"), nullable=False, default="not-full")

    hall_relationship = relationship("Hall", back_populates="floors")
    user_floor = relationship("User", back_populates="floor_relationship")