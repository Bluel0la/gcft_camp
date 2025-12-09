from pydantic import BaseModel, ConfigDict, Field
from enum import Enum
from typing import Optional
from datetime import date
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
    medical_issues: Optional[str] = None
    local_assembly: Optional[str] = None
    local_assembly_address: Optional[str] = None
    hall_name: Optional[str] = None
    floor: Optional[str] = None
    bed_number: Optional[str] = None
    extra_beds: Optional[list[int]] = None  # Add this line


class UserRegistration(UserBase):
    pass


class UserView(UserBase):
    id: int
    gender: str
    phone_number: Optional[str] = Field(default=None)

    class Config:
        orm_mode = True


class UserDisplay(UserView):
    pass


class UserSummary(BaseModel):
    id: int
    first_name: str
    category: str
    hall_name: str
    floor: str
    bed_number: str
    extra_beds: Optional[list[int]] = None
    phone_number: str


    model_config = ConfigDict(from_attributes=True)
