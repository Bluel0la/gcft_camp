from pydantic import BaseModel, ConfigDict, Field
from enum import Enum
from typing import Optional
from datetime import date
from fastapi import Form
from uuid import UUID
class AgeRangeEnum(str, Enum):
    age_10_17 = "10-17"
    age_18_25 = "18-25"
    age_26_35 = "26-35"
    age_36_45 = "36-45"
    age_45_55 = "45-55"
    age_56_65 = "56-65"
    age_66_70 = "66-70"
    age_71_plus = "71+"


class UserBase(BaseModel):
    category: str
    first_name: str
    age_range: AgeRangeEnum
    marital_status: str
    no_children: Optional[int] = None
    names_children: Optional[str] = None
    country: str
    state: str
    arrival_date: date
    profile_picture_url: Optional[str] = None
    medical_issues: Optional[str] = None
    local_assembly: Optional[str] = None
    local_assembly_address: Optional[str] = None
    hall_name: Optional[str] = None
    floor: Optional[str] = None
    bed_number: Optional[str] = None
    active_status: Optional[str] = None
    extra_beds: Optional[list[str]] = None  


class UserRegistration(UserBase):

    @classmethod
    def as_form(
        cls,
        category: str = Form(...),
        first_name: str = Form(...),
        age_range: AgeRangeEnum = Form(...),
        marital_status: str = Form(...),
        no_children: Optional[int] = Form(None),
        names_children: Optional[str] = Form(None),
        country: str = Form(...),
        state: str = Form(...),
        arrival_date: date = Form(...),
        medical_issues: Optional[str] = Form(None),
        local_assembly: Optional[str] = Form(None),
        local_assembly_address: Optional[str] = Form(None),
    ) -> "UserRegistration":
        return cls(
            category=category,
            first_name=first_name,
            age_range=age_range,
            marital_status=marital_status,
            no_children=no_children,
            names_children=names_children,
            country=country,
            state=state,
            arrival_date=arrival_date,
            medical_issues=medical_issues,
            local_assembly=local_assembly,
            local_assembly_address=local_assembly_address,
        )


class UserView(UserBase):
    id: int
    gender: str
    phone_number: Optional[str] = Field(default=None)

    class Config:
        orm_mode = True


class UserDisplay(UserView):
    
    class Config:
        orm_mode = True
        from_attributes = True
    pass


class UserSummary(BaseModel):
    id: int
    first_name: str
    category: str
    hall_name: str
    floor: str
    bed_number: str
    extra_beds: Optional[list[str]] = None
    phone_number: str
    profile_picture_url: str
    active_status: str


    model_config = ConfigDict(from_attributes=True)
