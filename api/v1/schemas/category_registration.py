from pydantic import BaseModel
from typing import Optional


class CategoryBase(BaseModel):
    category_name: str
    hall_name: str
    floor_allocated: int
    no_beds: int


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    hall_name: Optional[str] = None
    floor_allocated: Optional[int] = None
    no_beds: Optional[int] = None


class CategoryView(CategoryBase):
    id: int

    class Config:
        orm_mode = True
