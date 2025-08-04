from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date


class UserBase(BaseModel):
    category: str
    first_name: str
    gender: str
    age: int
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
    floor: Optional[int] = None
    bed_number: Optional[int] = None


class UserRegistration(UserBase):
    pass


class UserView(UserBase):
    id: int
    hall_name: Optional[str]
    floor: Optional[int]
    bed_number: Optional[int]
    phone_number: Optional[str] = Field(default=None)

    class Config:
        orm_mode = True


class UserDisplay(UserView):
    display_floor: Optional[str] = Field(default=None)
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_display(cls, obj, phone_number: Optional[str] = None):
        base = cls.from_orm(obj)
        floor_map = {
            0: "Ground Floor",
            1: "First Floor",
            2: "Second Floor",
            3: "Third Floor",
            4: "Fourth Floor",
            5: "Fifth Floor",
        }
        base.display_floor = floor_map.get(base.floor, f"Floor {base.floor}")
        base.phone_number = phone_number
        return base


class UserSummary(BaseModel):
    phone_number: str
    hall_name: str
    floor: int
    display_floor: str
    bed_number: int

    model_config = ConfigDict(from_attributes=True)
