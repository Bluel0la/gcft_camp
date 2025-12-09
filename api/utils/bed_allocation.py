from api.v1.schemas.floor_management import FloorCreateSchema
from api.v1.models.floor import HallFloors
from typing import Optional


def beds_required(
    no_children: Optional[int],
    last_assigned_bed: int,
    counter_value: int,
    bunk_size: int = 2,
) -> tuple[str, int, int]:
    """
    Returns the next available bed label (e.g., '1a', '1b', '2a', ...) and updates counters.
    """
    # Calculate sub-bed letter
    sub_bed_letter = chr(ord("a") + counter_value)
    bed_label = f"{last_assigned_bed}{sub_bed_letter}"

    # Update counter and bed number for next assignment
    next_counter = counter_value + 1
    next_bed = last_assigned_bed
    if next_counter >= bunk_size:
        next_counter = 0
        next_bed += 1

    return bed_label, next_bed, next_counter


def floor_create_logic(floor_no: int, hall_id: str, no_beds: Optional[int]) -> FloorCreateSchema:
    if no_beds is None:
        no_beds = 0
    return FloorCreateSchema(
        floor_no=floor_no,
        hall_id=hall_id,
        no_beds=no_beds
    )


def gender_classifier(category: str) -> str:
    """
    Checks the users category to see if it contains words like brothers, brother, male, female, sisters, mothers
    and if it does return the appropriate gender either male or female
    """
    
    category_lower = category.lower()
    if any(
        keyword in category_lower
        for keyword in ["brother", "brothers", "male"]
    ):
        return "male"
    elif any(
        keyword in category_lower
        for keyword in ["sister", "sisters", "mother", "mothers", "female"]
    ):
        return "female"
    return "unspecified"