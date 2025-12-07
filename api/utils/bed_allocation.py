from api.v1.schemas.floor_management import FloorCreateSchema
from typing import Optional


def beds_required(no_children: Optional[int], assigned_bed: int) -> list[int]:
    if not no_children or no_children < 2:
        return [assigned_bed]
    # Assign main bed and one extra bed (next available)
    return [assigned_bed, assigned_bed + 1]


def floor_create_logic(floor_no: int, hall_id: str, no_beds: Optional[int]) -> FloorCreateSchema:
    if no_beds is None:
        no_beds = 0
    return FloorCreateSchema(
        floor_no=floor_no,
        hall_id=hall_id,
        no_beds=no_beds
    )
