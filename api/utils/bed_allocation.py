from api.v1.schemas.floor_management import FloorCreateSchema
from api.v1.models.phone_number import PhoneNumber
from api.v1.models.floor import HallFloors
from typing import Optional, List, Tuple
from api.v1.models.user import User
from api.v1.models.hall import Hall
from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import case, and_
import re


def beds_required(
    no_children: Optional[int],
    last_assigned_bed: int,
    counter_value: int,
    bunk_size: int = 2,
) -> Tuple[List[str], int, int]:
    """
    Returns allocated bed labels and updated counters.

    - Allocates 1 bed if children < 2
    - Allocates 4 beds if children >= 2
    """

    beds_needed = 4 if no_children is not None and no_children >= 2 else 1
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
    return FloorCreateSchema(floor_no=floor_no, hall_id=hall_id, no_beds=no_beds)


def gender_classifier(category: str) -> str:
    """
    Classifies gender based on whole-word matches in a category string.
    """

    category_lower = category.lower()

    male_pattern = r"\b(brother|brothers|male)\b"
    female_pattern = r"\b(sister|sisters|mother|mothers|female)\b"

    if re.search(female_pattern, category_lower):
        return "female"
    elif re.search(male_pattern, category_lower):
        return "male"
    return "unspecified"


def validate_gender(category: str) -> str:
    gender = gender_classifier(category)
    if gender not in {"male", "female"}:
        raise HTTPException(status_code=400, detail="Invalid gender classification")
    return gender


def fetch_user_information_for_reallocation(
    db: Session,
    late_comers_number: str,
    no_children: int,
) -> Tuple[Hall, HallFloors, List[str]]:

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
            status_code=404,
            detail="No user registered with this number.",
        )

    beds: List[str] = [user_record.bed_number]

    # Include extra beds only if no_children > 2
    if no_children > 2 and user_record.extra_beds:
        beds.extend(user_record.extra_beds)

    return (
        user_record.hall,
        user_record.floor,
        beds,
    )


def allocate_bed(db: Session, gender: str, payload):
    eligible_halls = (
        db.query(Hall)
        .filter((Hall.gender == gender) | (Hall.hall_name == "Jerusalem Hall"))
        .all()
    )
    last_hall = None
    for hall in eligible_halls:
        floors = (
            db.query(HallFloors)
            .filter(
                HallFloors.hall_id == hall.id,
                HallFloors.status == "not-full",
                # STRICT conditions
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

    return None, last_hall, None


def allocate_backup_bed(db: Session, gender: str, payload):
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

            # Lock users implicitly by querying under the same transaction
            #Filter users on the floor to get occupied child slots
            occupied_slots = {
                user.bed_number
                for user in (
                    db.query(User).filter(
                        User.floor == floor.floor_id,
                        User.bed_number.ilike("%c"),
                    ).with_for_update().all()
                )
            }
            
            all_slots = [f"{i}c" for i in range(1, max_child_slots + 1)]
            available_slots = [slot for slot in all_slots if slot not in occupied_slots]

            if not available_slots:
                floor.status = "full"
                continue

            # Allocate lowest available child slot
            assigned_slot = available_slots[0]

            return hall, floor, [assigned_slot]

    return None, None, None


# function to update a users information
def update_lateuser_information(db: Session, phone: str):
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

    # delete the users record
    db.delete(user_record)
    db.delete(phone_record)
    db.commit()


def compute_hall_statistics(db: Session, hall: Hall) -> dict:
    floors = db.query(HallFloors).filter(HallFloors.hall_id == hall.id).all()

    total_beds = sum(floor.no_beds for floor in floors)

    all_users_count = 0
    active_users_count = 0

    for floor in floors:
        all_users_count += db.query(User).filter(User.floor == floor.floor_id).count()

        active_users_count += (
            db.query(User)
            .filter(User.floor == floor.floor_id, User.active_status == "active")
            .count()
        )

    return {
        "total_beds": total_beds,
        "all_users_count": all_users_count,
        "active_users_count": active_users_count,
        "remaining_space": total_beds - all_users_count,
    }
