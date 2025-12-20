from api.v1.schemas.floor_management import FloorCreateSchema
from api.v1.models.hall import Hall
from sqlalchemy.orm import Session
from api.v1.models.floor import HallFloors
from typing import Optional, List, Tuple
from sqlalchemy import or_

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


def allocate_bed(
    db: Session,
    gender: str,
    payload,
):
    eligible_halls = (
        db.query(Hall)
        .filter((Hall.gender == gender) | (Hall.hall_name == "Jerusalem Hall"))
        .order_by(Hall.hall_name)
        .all()
    )

    for hall in eligible_halls:
        floors = (
            db.query(HallFloors)
            .filter(
                HallFloors.hall_id == hall.id,
                HallFloors.status == "not-full",
                or_(
                    HallFloors.age_ranges.contains([payload.age_range]),
                    HallFloors.age_ranges.is_(None),
                    HallFloors.age_ranges == [],
                ),
                or_(
                    HallFloors.categories.any(category_name=payload.category),
                    ~HallFloors.categories.any(),
                ),
            )
            .order_by(HallFloors.floor_no)
            .with_for_update()  # 🔐 critical lock
            .all()
        )

        for floor in floors:
            bunk_size = 2
            floor.last_assigned_bed = floor.last_assigned_bed or 1
            floor.counter_value = floor.counter_value or 0

            total_beds = floor.no_beds * bunk_size
            assigned = ((floor.last_assigned_bed - 1) * bunk_size) + floor.counter_value

            if assigned < total_beds:
                beds, next_bed, next_counter = beds_required(
                    payload.no_children,
                    floor.last_assigned_bed,
                    floor.counter_value,
                    bunk_size,
                )

                floor.last_assigned_bed = next_bed
                floor.counter_value = next_counter

                if (((next_bed - 1) * bunk_size) + next_counter) >= total_beds:
                    floor.status = "full"

                return hall, floor, beds

    return None, None, None
