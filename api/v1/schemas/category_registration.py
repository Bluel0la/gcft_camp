from pydantic import BaseModel
from typing import Optional, List


class CategoryBase(BaseModel):
    category_name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    category_name: Optional[str] = None
class CategoryView(BaseModel):
    id: int
    category_name: str
    

    class Config:
        orm_mode = True
