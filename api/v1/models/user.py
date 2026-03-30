from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, JSON, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Programme linkage
    programme_id = Column(Integer, ForeignKey("programmes.id"), nullable=False)

    # Phone linkage (one phone → many users for parent/child sharing)
    phone_number_id = Column(Integer, ForeignKey("phone_numbers.id"), nullable=False)

    # Registration metadata
    registration_type = Column(
        Enum("attendance_only", "with_accommodation", name="registration_type_enum"),
        nullable=False,
    )
    registration_completed = Column(Boolean, default=False, nullable=False)

    # Personal info
    category = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    age_range = Column(
        Enum(
            "10-17", "18-25", "26-35", "36-45",
            "46-55", "56-65", "66-70", "71+",
            name="age_range_enum",
        ),
        nullable=False,
        default="18-25",
    )
    marital_status = Column(String, nullable=False)
    no_children = Column(Integer, nullable=True, default=0)
    names_children = Column(String, nullable=True)
    country = Column(String, nullable=False)
    state = Column(String, nullable=False)
    arrival_date = Column(Date, nullable=False)
    date_verified = Column(Date, nullable=True)
    medical_issues = Column(String, nullable=True)
    local_assembly = Column(String, nullable=True)
    local_assembly_address = Column(String, nullable=True)

    # Accommodation fields (only populated for with_accommodation registrations)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=True)
    floor_id = Column(ForeignKey("hall_floors.floor_id"), nullable=True)
    bed_number = Column(String, nullable=True)
    extra_beds = Column(JSON, nullable=True)

    # Profile
    profile_picture_url = Column(String, nullable=True)
    object_key = Column(String, unique=True, nullable=False)
    date_presigned_url_generated = Column(Date, nullable=False)

    # Status
    active_status = Column(
        Enum("active", "inactive", "relocated", name="active_status_enum"),
        default="inactive",
        nullable=False,
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    phone = relationship("PhoneNumber", back_populates="users")
    programme = relationship("Programme", back_populates="registrations")
    hall = relationship("Hall", back_populates="residents", foreign_keys=[hall_id])
    floor_relationship = relationship("HallFloors", back_populates="user_floor")
