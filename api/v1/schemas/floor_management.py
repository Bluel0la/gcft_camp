from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class FloorCreateSchema(BaseModel):
    floor_no: int = Field(..., description="The number of the floor")
    hall_id: int = Field(..., description="The ID of the hall the floor belongs to")
    no_beds: int = Field(0, description="The number of beds on the floor")

class FloorUpdateSchema(BaseModel):
    floor_no: Optional[int] = Field(None, description="The number of the floor")
    age_range: Optional[str] = Field(None, description="The age range of people staying on the floor the floor")
    categories: Optional[list[int]] = Field(None, description="List of category IDs for the floor")
    no_beds: Optional[int] = Field(None, description="The number of beds on the floor")

class FloorViewSchema(BaseModel):
    floor_id: UUID = Field(..., description="The unique identifier of the floor")
    floor_no: int = Field(..., description="The number of the floor")
    hall_id: int = Field(..., description="The ID of the hall the floor belongs to")
    categories: Optional[list[int]] = Field(None, description="List of category IDs for the floor")
    no_beds: int = Field(..., description="The number of beds on the floor")
    status: str = Field(..., description="The status of the floor (full/not-full)")
    
    class Config:
        orm_mode = True
        from_attributes = True
