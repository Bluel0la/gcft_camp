from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.db.database import Base


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, nullable=False)
    is_parent = Column(Boolean, default=False, nullable=False)
    time_registered = Column(DateTime(timezone=True), server_default=func.now())

    # One phone number can be shared by multiple users (parent + children)
    users = relationship("User", back_populates="phone")
