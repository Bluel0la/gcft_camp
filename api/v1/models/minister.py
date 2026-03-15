from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint, Sequence, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.db.database import Base

meal_id_seq = Sequence("meal_id_sequence", start=000)

class Minister(Base):
    __tablename__ = "ministers"

    id = Column(Integer, primary_key=True, index=True)
    identification_meal_number = Column(
        Integer,
        meal_id_seq,
        server_default=meal_id_seq.next_value(),
        unique=True,
    )
    phone_number = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    category = Column(String, nullable=False, default="minister")
    medical_issues = Column(String, nullable=True, default="None")
    local_assembly = Column(String, nullable=True)
    local_assembly_address = Column(String, nullable=True)

    room_number = Column(String, nullable=True)
    # Hall and bed allocation fields
    hall_name = Column(String, ForeignKey("halls.hall_name"), nullable=True)
    floor = Column(ForeignKey("hall_floors.floor_id"), nullable=True)
    bed_number = Column(String, nullable=True)
    
    profile_picture_url = Column(String, nullable=True, default="getalife")
    object_key = Column(String, unique=True, nullable=False)
    date_presigned_url_generated = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    meal_records = relationship("MealRecord", back_populates="minister", cascade="all, delete-orphan")


# api/v1/models/minister.py


class MealRecord(Base):
    __tablename__ = "meal_records"

    id = Column(Integer, primary_key=True, index=True)
    minister_id = Column(Integer, ForeignKey("ministers.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    # New field: e.g., "breakfast", "lunch", "dinner"
    meal_type = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    minister = relationship("Minister", back_populates="meal_records")

    __table_args__ = (
        # Now allows 1 breakfast, 1 lunch, and 1 dinner per day
        UniqueConstraint(
            "minister_id", "date", "meal_type", name="uq_minister_meal_session"
        ),
    )
