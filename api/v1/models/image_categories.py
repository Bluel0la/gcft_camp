from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from api.db.database import Base

class ImageCategory(Base):
    __tablename__ = "image_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, unique=True, nullable=False)
    
    images = relationship("Image", back_populates="image_category")