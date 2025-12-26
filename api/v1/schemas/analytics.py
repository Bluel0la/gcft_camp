from pydantic import BaseModel
from typing import List, Dict



class HallAnalytics(BaseModel):
    hall_name: str
    no_floors: int
    total_beds: int
    booked_beds: int
    free_beds: int
    verified_users: int


class UserCount(BaseModel):
    total_users: int
