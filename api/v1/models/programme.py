from sqlalchemy import Column, Integer, String, Date, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.db.database import Base


class Programme(Base):
    __tablename__ = "programmes"

    id = Column(Integer, primary_key=True, index=True)
    programme_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    close_date = Column(Date, nullable=False)
    registration_status = Column(
        Enum("open", "closed", "suspended", name="registration_status_enum"),
        default="open",
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    registrations = relationship("User", back_populates="programme")
