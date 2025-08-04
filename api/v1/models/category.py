from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from api.db.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, nullable=False)
    hall_name = Column(String, ForeignKey("halls.hall_name"), nullable=False)
    floor_allocated = Column(Integer, nullable=False)
    no_beds = Column(Integer, nullable=False)

    hall = relationship("Hall", back_populates="categories")
