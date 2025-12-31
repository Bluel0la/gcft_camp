from sqlalchemy import Column, String, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from api.db.database import Base

class Image(Base):
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    image_name = Column(String, unique=True, nullable=False)
    image_url = Column(String, unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("image_categories.id"), nullable=False)
    status = Column(Enum("in-use", "inactive", name="image_status_enum"), default="in-use", nullable=False)
    object_key = Column(String)
    image_category = relationship("ImageCategory", back_populates="images")