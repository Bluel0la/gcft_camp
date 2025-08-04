from pydantic import BaseModel, root_validator
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


class UserView(UserRegistration):
    id: int
    hall_name: Optional[str]
    floor: Optional[int]
    bed_number: Optional[int]
    phone_number: Optional[str]
    display_floor: Optional[str] = None  # ⬅️ new field

    @root_validator(pre=True)
    def map_display_floor(cls, values):
        floor_number = values.get("floor", None)
        if floor_number is not None:
            floor_map = {
                0: "Ground Floor",
                1: "First Floor",
                2: "Second Floor",
                3: "Third Floor",
                4: "Fourth Floor",
                5: "Fifth Floor",
            }
            values["display_floor"] = floor_map.get(
                floor_number, f"Floor {floor_number}"
            )
        return values

    class Config:
        orm_mode = True
