from sqlalchemy import Table, Column, Integer, ForeignKey, Enum, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from api.db.database import Base
from sqlalchemy.dialects.postgresql import ARRAY

# Association table for many-to-many relationship
floor_category_association = Table(
    "floor_category_association",
    Base.metadata,
    Column("floor_id", UUID(as_uuid=True), ForeignKey("hall_floors.floor_id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"))
)

class HallFloors(Base):
    __tablename__ = "hall_floors"

    floor_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    hall_id = Column(ForeignKey("halls.id"), nullable=False)
    floor_no = Column(Integer, nullable=False)
    age_ranges = Column(ARRAY(String), nullable=True)

    # Many-to-many relationship
    categories = relationship("Category", secondary=floor_category_association, back_populates="floors")

    no_beds = Column(Integer, nullable=True, default=0)
    last_assigned_bed = Column(Integer, nullable=True, default=0)
    status = Column(Enum("full", "not-full", name="floor_status"), nullable=False, default="not-full")
    counter_value = Column(Integer, nullable=True, default=0)

    hall_relationship = relationship("Hall", back_populates="floors")
    user_floor = relationship("User", back_populates="floor_relationship")
