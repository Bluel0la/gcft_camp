from pydantic import BaseModel
from typing import Optional


class HallBase(BaseModel):
    hall_name: str
    gender: str
    no_floors: int


class HallCreate(HallBase):
    pass


class HallUpdate(BaseModel):
    hall_name: Optional[str] = None
    gender: Optional[str] = None
    no_floors: Optional[int] = None


class HallView(HallBase):
    id: int

    class Config:
        orm_mode = True