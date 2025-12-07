from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from api.db.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, nullable=False)
    
    floors = relationship("HallFloors", secondary="floor_category_association", back_populates="categories")

