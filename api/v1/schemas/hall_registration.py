from pydantic import BaseModel
from typing import Optional


class HallBase(BaseModel):
    hall_name: str
    no_beds: int
    category_allocated: Optional[str]
    no_floors: int


class HallCreate(HallBase):
    pass


class HallUpdate(BaseModel):
    hall_name: Optional[str] = None
    no_beds: Optional[int] = None
    category_allocated: Optional[str] = None
    no_floors: Optional[int] = None


class HallView(HallBase):
    id: int

    class Config:
        orm_mode = True