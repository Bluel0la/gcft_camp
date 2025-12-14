from api.v1.schemas.floor_management import FloorCreateSchema
from api.v1.models.floor import HallFloors
from typing import Optional, List, Tuple


def beds_required(
    no_children: Optional[int],
    last_assigned_bed: int,
    counter_value: int,
    bunk_size: int = 2,
) -> Tuple[List[str], int, int]:
    """
    Returns allocated bed labels and updated counters.

    - Allocates 1 bed if children < 2
    - Allocates 2 beds if children >= 2
    """

    beds_needed = 2 if no_children is not None and no_children >= 2 else 1
    allocated_beds: List[str] = []

    for _ in range(beds_needed):
        # Calculate sub-bed letter (a, b, ...)
        sub_bed_letter = chr(ord("a") + counter_value)
        bed_label = f"{last_assigned_bed}{sub_bed_letter}"
        allocated_beds.append(bed_label)

        # Update counters
        counter_value += 1
        if counter_value >= bunk_size:
            counter_value = 0
            last_assigned_bed += 1

    return allocated_beds, last_assigned_bed, counter_value


def floor_create_logic(
    floor_no: int, hall_id: str, no_beds: Optional[int]
) -> FloorCreateSchema:
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
