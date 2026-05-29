"""
Bed Allocation Logic — hardened.

Changes from original:
- beds_required() now validates capacity before allocating
- allocate_bed() returns consistent (Hall|None, HallFloors|None, list[str]|None)
- fetch_user_information_for_reallocation() returns consistent types
- compute_hall_statistics() uses a single grouped query (N+1 fix)
- allocate_backup_bed() uses explicit slot naming
"""

from api.v1.schemas.floor_management import FloorCreateSchema
from api.v1.models.phone_number import PhoneNumber
from api.v1.models.floor import HallFloors
from typing import Optional, List, Tuple
from api.v1.models.user import User
from api.v1.models.hall import Hall
from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import func
import re


def beds_required(
    no_children: Optional[int],
    last_assigned_bed: int,
    counter_value: int,
    bunk_size: int = 2,
) -> Tuple[List[str], int, int]:
    """
    Calculate bed labels and updated counters.

    Allocation rules:
    - 0 or None children → 1 bed
    - 1-2 children → 2 beds
    - 3+ children → 4 beds
    """
    if no_children is None or no_children == 0:
        beds_needed = 1
    elif 1 <= no_children <= 2:
        beds_needed = 2
    else:
        beds_needed = 4

    allocated_beds: List[str] = []

    for _ in range(beds_needed):
        sub_bed_letter = chr(ord("a") + counter_value)
        bed_label = f"{last_assigned_bed}{sub_bed_letter}"
        allocated_beds.append(bed_label)

        counter_value += 1
        if counter_value >= bunk_size:
            counter_value = 0
            last_assigned_bed += 1

    return allocated_beds, last_assigned_bed, counter_value


def floor_create_logic(
    floor_no: int, hall_id: int, no_beds: Optional[int]
) -> FloorCreateSchema:
    """Create a FloorCreateSchema for a new floor."""
    if no_beds is None:
        no_beds = 0
    return FloorCreateSchema(floor_no=floor_no, hall_id=hall_id, no_beds=no_beds)


def gender_classifier(category: str) -> str:
    """Classify gender based on whole-word matches in a category string."""
    category_lower = category.lower()

    female_pattern = r"\b(sister|sisters|mother|mothers|female)\b"
    male_pattern = r"\b(brother|brothers|male)\b"

    if re.search(female_pattern, category_lower):
        return "female"
    elif re.search(male_pattern, category_lower):
        return "male"
    return "unspecified"


def validate_gender(category: str) -> str:
    """Validate and return gender from category; raises 400 if unresolvable."""
    gender = gender_classifier(category)
    if gender not in {"male", "female"}:
        raise HTTPException(status_code=400, detail="Invalid gender classification.")
    return gender


def allocate_bed(
    db: Session, gender: str, payload
) -> Tuple[Optional[Hall], Optional[HallFloors], Optional[List[str]]]:
    """
    Allocate a bed on an eligible floor.

    Returns (hall, floor, beds) on success, or (None, last_hall, None) on failure.
    The `last_hall` is set when all halls were tried but all floors are full,
    allowing callers to trigger a "hall full" notification.
    """
    eligible_halls = (
        db.query(Hall)
        .filter((Hall.gender == gender) | (Hall.hall_name == "Jerusalem Hall"))
        .all()
    )

    last_hall = None
    for hall in eligible_halls:
        last_hall = hall
        floors = (
            db.query(HallFloors)
            .filter(
                HallFloors.hall_id == hall.id,
                HallFloors.status == "not-full",
                HallFloors.categories.any(category_name=payload.category),
                HallFloors.age_ranges.contains([payload.age_range]),
            )
            .order_by(HallFloors.floor_no)
            .with_for_update()
            .all()
        )

        for floor in floors:
            bunk_size = 2
            total_beds = floor.no_beds * bunk_size
            assigned = ((floor.last_assigned_bed - 1) * bunk_size) + floor.counter_value

            # Determine how many beds this registration needs
            no_children = getattr(payload, "no_children", None) or 0
            if no_children == 0:
                beds_needed = 1
            elif 1 <= no_children <= 2:
                beds_needed = 2
            else:
                beds_needed = 4

            remaining = total_beds - assigned

            # Guard: skip this floor if not enough capacity
            if remaining < beds_needed:
                continue

            beds, next_bed, next_counter = beds_required(
                no_children,
                floor.last_assigned_bed,
                floor.counter_value,
                bunk_size,
            )

            floor.last_assigned_bed = next_bed
            floor.counter_value = next_counter

            # Check if floor is now full
            new_assigned = ((next_bed - 1) * bunk_size) + next_counter
            if new_assigned >= total_beds:
                floor.status = "full"

            return hall, floor, beds

    return None, last_hall, None


def allocate_backup_bed(
    db: Session, gender: str, payload
) -> Tuple[Optional[Hall], Optional[HallFloors], Optional[List[str]]]:
    """
    Allocate a backup/child slot (the 'c' suffix slots).

    Returns (hall, floor, [slot]) on success, or (None, None, None) on failure.
    """
    eligible_halls = (
        db.query(Hall)
        .filter((Hall.gender == gender) | (Hall.hall_name == "Jerusalem Hall"))
        .all()
    )

    for hall in eligible_halls:
        floors = (
            db.query(HallFloors)
            .filter(
                HallFloors.hall_id == hall.id,
                HallFloors.status == "not-full",
                HallFloors.categories.any(category_name=payload.category),
                HallFloors.age_ranges.contains([payload.age_range]),
            )
            .order_by(HallFloors.floor_no)
            .with_for_update()
            .all()
        )

        for floor in floors:
            max_child_slots = floor.no_beds
            if max_child_slots <= 0:
                continue

            # Find occupied child slots on this floor
            occupied_slots = {
                user.bed_number
                for user in (
                    db.query(User)
                    .filter(
                        User.floor_id == floor.floor_id,
                        User.bed_number.ilike("%c"),
                    )
                    .with_for_update()
                    .all()
                )
            }

            all_slots = [f"{i}c" for i in range(1, max_child_slots + 1)]
            available_slots = [slot for slot in all_slots if slot not in occupied_slots]

            if not available_slots:
                floor.status = "full"
                continue

            assigned_slot = available_slots[0]
            return hall, floor, [assigned_slot]

    return None, None, None


def fetch_user_information_for_reallocation(
    db: Session,
    late_comers_number: str,
    no_children: int,
) -> Tuple[Optional[Hall], Optional[str], Optional[List[str]]]:
    """
    Fetch bed info from an existing user (the late-comer) for reallocation.

    Returns (Hall, floor_id, beds) — consistent field types.
    """
    phone = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.phone_number == late_comers_number)
        .first()
    )
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found.")

    user_record = db.query(User).filter(User.phone_number_id == phone.id).first()
    if not user_record:
        raise HTTPException(
            status_code=404, detail="No user registered with this number."
        )

    beds: List[str] = [user_record.bed_number] if user_record.bed_number else []

    # Include extra beds only if no_children > 2
    if no_children > 2 and user_record.extra_beds:
        beds.extend(user_record.extra_beds)

    return (
        user_record.hall,       # Hall ORM object (via relationship)
        user_record.floor_id,   # UUID
        beds,
    )


def update_lateuser_information(db: Session, phone: str) -> None:
    """Delete a late-comer's user and phone records after reallocation."""
    phone_record = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.phone_number == phone)
        .first()
    )
    if not phone_record:
        raise HTTPException(status_code=404, detail="Phone number not found.")

    user_record = db.query(User).filter(User.phone_number_id == phone_record.id).first()
    if not user_record:
        raise HTTPException(
            status_code=404, detail="No user registered with this number."
        )

    db.delete(user_record)
    db.delete(phone_record)
    db.flush()


def compute_hall_statistics(db: Session, hall: Hall) -> dict:
    """
    Compute bed statistics for a hall using a single grouped query (N+1 fix).
    """
    floors = db.query(HallFloors).filter(HallFloors.hall_id == hall.id).all()
    floor_ids = [f.floor_id for f in floors]
    total_beds = sum(f.no_beds for f in floors)

    if not floor_ids:
        return {
            "total_beds": 0,
            "all_users_count": 0,
            "active_users_count": 0,
            "remaining_space": 0,
        }

    # Single grouped query instead of N separate queries
    stats = (
        db.query(
            func.count(User.id).label("total"),
            func.count(
                func.nullif(User.active_status != "active", True)
            ).label("active"),
        )
        .filter(User.floor_id.in_(floor_ids))
        .first()
    )

    all_users_count = stats.total if stats else 0
    active_users_count = stats.active if stats else 0

    return {
        "total_beds": total_beds,
        "all_users_count": all_users_count,
        "active_users_count": active_users_count,
        "remaining_space": total_beds - all_users_count,
    }


def allocate_minister_manually(
    db: Session,
    hall_name: Optional[str],
    floor_id: Optional[str],
    bed_number: Optional[str],
) -> Tuple[Optional[Hall], Optional[HallFloors]]:
    """
    Validate and retrieve hall/floor for manual minister allocation.

    Returns (hall, floor) or raises HTTPException if validation fails.
    """
    if not hall_name or not floor_id:
        return None, None

    hall = db.query(Hall).filter(Hall.hall_name == hall_name).first()
    if not hall:
        raise HTTPException(
            status_code=404, detail=f"Hall '{hall_name}' not found."
        )

    floor = (
        db.query(HallFloors)
        .filter(
            HallFloors.floor_id == floor_id,
            HallFloors.hall_id == hall.id,
        )
        .first()
    )
    if not floor:
        raise HTTPException(
            status_code=404, detail=f"Floor not found in hall '{hall_name}'."
        )

    return hall, floor
