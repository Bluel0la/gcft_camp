from sqlalchemy import Column, Integer, String, Date, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from api.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number_id = Column(Integer, ForeignKey("phone_numbers.id"), nullable=False)
    category = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    age_range = Column(Enum("10-17", "18-25", "26-35", "36-45", "45-55", "56-65", "66-70", "71+", name="age_range_enum"), nullable=False, default="18-25")
    marital_status = Column(String, nullable=False)
    no_children = Column(Integer, nullable=True)
    names_children = Column(String, nullable=True)
    country = Column(String, nullable=False)
    state = Column(String, nullable=False)
    arrival_date = Column(Date, nullable=False)
    date_verified = Column(Date, nullable=True)
    medical_issues = Column(String, nullable=True)
    local_assembly = Column(String, nullable=True)
    local_assembly_address = Column(String, nullable=True)
    hall_name = Column(String, ForeignKey("halls.hall_name"), nullable=True)
    floor = Column(ForeignKey("hall_floors.floor_id"), nullable=True)
    bed_number = Column(String, nullable=True)
    extra_beds = Column(JSON, nullable=True)
    profile_picture_url = Column(String, nullable=True, default="getalife")
    active_status = Column(Enum("active", "inactive", "relocated", name="active_status_enum"), default="inactive", nullable=False)

    phone = relationship("PhoneNumber", back_populates="user")
    hall = relationship("Hall", back_populates="residents")
    floor_relationship = relationship("HallFloors", back_populates="user_floor")
