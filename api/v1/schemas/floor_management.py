from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from enum import Enum


class FloorUpdateField(str, Enum):
    categories = "categories"
    age_ranges = "age_ranges"


class FloorUpdateOperation(str, Enum):
    add = "add"
    remove = "remove"

class FloorUpdatePayload(BaseModel):
    field: FloorUpdateField
    operation: FloorUpdateOperation

    category_ids: Optional[List[int]] = None
    age_ranges: Optional[List[str]] = None


class FloorCreateSchema(BaseModel):
    floor_no: int = Field(..., description="The number of the floor")
    hall_id: int = Field(..., description="The ID of the hall the floor belongs to")
    no_beds: int = Field(0, description="The number of beds on the floor")

class FloorBedUpdate(BaseModel):
    no_beds: Optional[int] = Field(None, description="The number of beds on the floor")

class FloorViewSchema(BaseModel):
    floor_id: UUID = Field(..., description="The unique identifier of the floor")
    floor_no: int = Field(..., description="The number of the floor")
    hall_id: int = Field(..., description="The ID of the hall the floor belongs to")
    categories: Optional[list[int]] = Field(None, description="List of category IDs for the floor")
    age_ranges: Optional[list[str]] = Field(None, description="List of age ranges for the floor")
    no_beds: int = Field(..., description="The number of beds on the floor")
    status: str = Field(..., description="The status of the floor (full/not-full)")
    
    class Config:
        orm_mode = True
        from_attributes = True
