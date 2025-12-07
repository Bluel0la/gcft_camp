from pydantic import BaseModel
from typing import List, Dict


class CategoryAnalytics(BaseModel):
    category_name: str
    floor_allocated: int
    total_beds: int
    beds_allocated: int
    beds_unallocated: int
    male_count: int
    female_count: int


class HallAnalytics(BaseModel):
    hall_name: str
    no_floors: int
    total_beds: int
    booked_beds: int
    free_beds: int
    signed_in_users: int
    female_count: int
    male_count: int
    male_active_count: int
    female_active_count: int


class UserCount(BaseModel):
    total_users: int
