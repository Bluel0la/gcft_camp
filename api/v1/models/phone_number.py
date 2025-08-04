from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from api.db.database import Base


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, nullable=False)
    time_registered = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="phone")
