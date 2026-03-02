from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional
from datetime import date, datetime
from fastapi import Form
from enum import Enum


class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"

class MinisterBase(BaseModel):
    phone_number: str
    first_name: str
    last_name: Optional[str] = None
    room_number: Optional[str] = None
    category: Optional[str] = None


class MinisterCreate(MinisterBase):
    medical_issues: Optional[str] = None
    local_assembly: Optional[str] = None
    local_assembly_address: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        phone_number: str = Form(...),
        first_name: str = Form(...),
        last_name: Optional[str] = Form(None),
        room_number: Optional[str] = Form(None),
        category: Optional[str] = Form(None),
        medical_issues: Optional[str] = Form(None),
        local_assembly: Optional[str] = Form(None),
        local_assembly_address: Optional[str] = Form(None),
    ):
        return cls(
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            room_number=room_number,
            category=category,
            medical_issues=medical_issues,
            local_assembly=local_assembly,
            local_assembly_address=local_assembly_address,
        )


class MinisterOut(MinisterBase):
    id: int
    identification_meal_number: int  # Added this field
    profile_picture_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MealMarkInput(BaseModel):
    phone_number: Optional[str] = None
    identification_meal_number: Optional[int] = None
    date: Optional[date] = None
    meal_type: MealType


class MealRecordOut(BaseModel):
    id: int
    minister_id: int
    date: date
    meal_type: str  # Included in output
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MinisterStatusOut(BaseModel):
    minister: MinisterOut
    total_meals_taken: int
    meal_dates: list[date]
