from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date
from enum import Enum
import sys

class AgeRangeEnum(str, Enum):
    age_10_17 = "10-17"
    age_18_25 = "18-25"
    age_26_35 = "26-35"

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

class UserView(UserBase):
    id: int
    gender: str
    phone_number: Optional[str] = Field(default=None)
    medical_issues: Optional[str] = Field(default=None)

    class Config:
        orm_mode = True

try:
    print(UserView(
        id=1,
        first_name="First",
        category="General",
        hall_name=None,
        floor=None,
        bed_number=None,
        extra_beds=[],
        phone_number="1234567890",
        gender="M",
        age_range=AgeRangeEnum.age_18_25,
        marital_status="Single",
        medical_issues=None,
        state="State",
        country="Country",
        arrival_date=date.today(),
        no_children=0,
        local_assembly=None,
        local_assembly_address=None,
        names_children=None,
        active_status="active",
        profile_picture_url=None
    ).model_dump())
    print("SUCCESS")
except Exception as e:
    print("ERROR:", e)
    sys.exit(1)
