from pydantic import BaseModel, Field
from typing import Optional, List


class ImageCategoryCreate(BaseModel):
    category_name: str = Field(..., example="Nature")


class ImageCategoryView(BaseModel):
    id: int
    category_name: str

    class Config:
        orm_mode = True


class ImageCreate(BaseModel):
    image_name: str = Field(..., example="Sunset")
    image_url: str = Field(..., example="https://example.com/sunset.jpg")
    category_id: int = Field(..., example=1)


class ImageView(BaseModel):
    id: int
    image_name: str
    image_url: str
    category_id: int
    status: str

    class Config:
        orm_mode = True
