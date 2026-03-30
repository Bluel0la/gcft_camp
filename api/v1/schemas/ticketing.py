from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, datetime
from fastapi import Form
from uuid import UUID
from api.v1.schemas.enums import AgeRangeEnum, MealType


class MinisterBase(BaseModel):
    phone_number: str
    first_name: str
    last_name: Optional[str] = None
    room_number: Optional[str] = None
    category: Optional[str] = None


class MinisterCreate(MinisterBase):
    gender: str
    age_range: AgeRangeEnum
    marital_status: str
    country: str
    state: str
    arrival_date: date
    medical_issues: Optional[str] = None
    local_assembly: Optional[str] = None
    local_assembly_address: Optional[str] = None
    # Manual hall allocation fields
    hall_name: Optional[str] = None
    floor_id: Optional[UUID] = Form(None)
    bed_number: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        phone_number: str = Form(...),
        first_name: str = Form(...),
        gender: str = Form(...),
        age_range: AgeRangeEnum = Form(...),
        marital_status: str = Form(...),
        country: str = Form(...),
        state: str = Form(...),
        arrival_date: date = Form(...),
        last_name: Optional[str] = Form(None),
        room_number: Optional[str] = Form(None),
        category: Optional[str] = Form(None),
        medical_issues: Optional[str] = Form(None),
        local_assembly: Optional[str] = Form(None),
        local_assembly_address: Optional[str] = Form(None),
        hall_name: Optional[str] = Form(None),
        floor_id: Optional[UUID] = Form(None),
        bed_number: Optional[str] = Form(None),
    ):
        return cls(
            phone_number=phone_number,
            first_name=first_name,
            gender=gender,
            age_range=age_range,
            marital_status=marital_status,
            country=country,
            state=state,
            arrival_date=arrival_date,
            last_name=last_name,
            room_number=room_number,
            category=category,
            medical_issues=medical_issues,
            local_assembly=local_assembly,
            local_assembly_address=local_assembly_address,
            hall_name=hall_name,
            floor_id=floor_id,
            bed_number=bed_number,
        )


class MinisterOut(MinisterBase):
    id: int
    identification_meal_number: int
    hall_name: Optional[str] = None
    floor: UUID | str | None = None
    bed_number: Optional[str] = None
    profile_picture_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MealMarkInput(BaseModel):
    phone_number: Optional[str] = None
    identification_meal_number: Optional[int] = None
    meal_date: Optional[date] = Field(None, alias="date")
    meal_type: MealType


class MealRecordOut(BaseModel):
    id: int
    minister_id: int
    meal_date: date = Field(alias="date")
    meal_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MinisterStatusOut(BaseModel):
    minister: MinisterOut
    total_meals_taken: int
    meal_dates: list[date]
