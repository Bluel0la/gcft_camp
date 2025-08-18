from pydantic import BaseModel
from typing import Optional, List


class CategoryBase(BaseModel):
    category_name: str
    hall_name: str
    floor_allocated: List[int]  # now accepts multiple floors
    no_beds: int


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    hall_name: Optional[str] = None
    floor_allocated: Optional[List[int]] = None  # also a list now
    no_beds: Optional[int] = None


class CategoryView(BaseModel):
    id: int
    category_name: str
    hall_name: str
    floor_allocated: int  # each record still has a single floor in DB
    no_beds: int

    class Config:
        orm_mode = True
