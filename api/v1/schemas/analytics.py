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
    categories: List[CategoryAnalytics]

class UserCount(BaseModel):
    total_users: int
