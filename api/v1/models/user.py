from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from api.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number_id = Column(Integer, ForeignKey("phone_numbers.id"), nullable=False)
    category = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    marital_status = Column(String, nullable=False)
    no_children = Column(Integer, nullable=True)
    names_children = Column(String, nullable=True)
    country = Column(String, nullable=False)
    state = Column(String, nullable=False)
    arrival_date = Column(Date, nullable=False)
    medical_issues = Column(String, nullable=True)
    local_assembly = Column(String, nullable=True)
    local_assembly_address = Column(String, nullable=True)
    hall_name = Column(String, ForeignKey("halls.hall_name"), nullable=True)
    floor = Column(Integer, nullable=True)
    bed_number = Column(Integer, nullable=True)

    phone = relationship("PhoneNumber", back_populates="user")
    hall = relationship("Hall", back_populates="residents")
