from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.schemas import phone_registration, registration, category_registration, hall_registration
from api.v1.services.full_halls import send_hall_full_email
from api.v1.models import phone_number, user, category, hall
from api.v1.models import hall as hall_model
from api.db.database import get_db
from api.utils.bed_allocation import beds_required
from datetime import datetime
import asyncio

registration_route = APIRouter(tags=["Hall Registration"])


@registration_route.post("/register-number", response_model=phone_registration.PhoneNumberView)
def register_phone_number(
    payload: phone_registration.PhoneNumberRegistration, db: Session = Depends(get_db)
):
    existing = (
        db.query(phone_number.PhoneNumber)
        .filter(phone_number.PhoneNumber.phone_number == payload.phone_number)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered.",
        )

    phone = phone_number.PhoneNumber(
        phone_number=payload.phone_number,
        time_registered=datetime.utcnow(),)

    db.add(phone)
    db.commit()
    db.refresh(phone)
    return phone


@registration_route.post(
    "/register-user/{number}", response_model=registration.UserDisplay
)
async def register_user(
    number: str, payload: registration.UserRegistration, db: Session = Depends(get_db)
):
    # Step 1: Check phone number
    phone = (
        db.query(phone_number.PhoneNumber)
        .filter(phone_number.PhoneNumber.phone_number == number)
        .first()
    )
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found.")

    # Step 2: Ensure user hasn't registered
    existing_user = (
        db.query(user.User).filter(user.User.phone_number_id == phone.id).first()
    )
    if existing_user:
        raise HTTPException(
            status_code=409, detail="User already registered with this phone number."
        )

    # Step 3: Get all category allocations (multi-floor)
    category_records = (
        db.query(category.Category)
        .filter(category.Category.category_name == payload.category)
        .order_by(category.Category.floor_allocated.asc())
        .all()
    )
    if not category_records:
        raise HTTPException(
            status_code=404, detail="No allocation found for this category."
        )

    beds_needed = beds_required(payload.no_children)
    floor_allocation = None
    assigned_beds = []
    hall_record = None

    # Step 4: Find next available beds
    for record in category_records:
        hall_record = (
            db.query(hall_model.Hall)
            .filter(hall_model.Hall.hall_name == record.hall_name)
            .first()
        )
        if (
            not hall_record
            or hall_record.no_allocated_beds + beds_needed > hall_record.no_beds
        ):
            continue  # skip if hall missing or insufficient space

        # Get already assigned bed numbers (including extra beds)
        taken = (
            db.query(user.User.bed_number, user.User.extra_beds)
            .filter(
                user.User.category == record.category_name,
                user.User.hall_name == record.hall_name,
                user.User.floor == record.floor_allocated,
            )
            .order_by(user.User.bed_number.asc())
            .all()
        )

        taken_numbers = set()
        for primary, extras in taken:
            if primary is not None:
                taken_numbers.add(primary)
            if extras:
                # Ensure extras is always treated as a list
                if isinstance(extras, list):
                    taken_numbers.update(extras)
                else:
                    # Fallback if stored as a JSON string
                    try:
                        import json

                        extra_list = json.loads(extras)
                        if isinstance(extra_list, list):
                            taken_numbers.update(extra_list)
                    except Exception:
                        pass  # ignore malformed data

        # Find first N free beds (not necessarily consecutive)
        free_beds = []
        for i in range(1, int(record.no_beds) + 1):
            if i not in taken_numbers:
                free_beds.append(i)
                if len(free_beds) == beds_needed:
                    break

        if len(free_beds) == beds_needed:
            assigned_beds = free_beds
            floor_allocation = record
            break

    if not floor_allocation or len(assigned_beds) != beds_needed:
        raise HTTPException(
            status_code=400,
            detail="No available beds for this category allocation or hall is full.",
        )

    # Step 5: Register user (store primary bed number; extra beds can be handled via a field)
    new_user = user.User(
        **payload.dict(exclude={"hall_name", "floor", "bed_number", "phone_number_id", "extra_beds"}),
        phone_number_id=phone.id,
        hall_name=floor_allocation.hall_name,
        floor=floor_allocation.floor_allocated,
        bed_number=assigned_beds[0],  # main bed
        extra_beds=(
            assigned_beds[1:] if len(assigned_beds) > 1 else None
        ),  # optional field
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Step 6: Increment hall allocated bed count by beds_needed
    if hall_record:
        hall_record.no_allocated_beds += beds_needed
        db.commit()
        db.refresh(hall_record)

        # If hall is now full, send alert email asynchronously
        if int(hall_record.no_allocated_beds) == int(hall_record.no_beds):
            asyncio.create_task(
                send_hall_full_email(hall_record, floor_allocation.category_name)
            )

    return registration.UserDisplay.from_orm_with_display(new_user, phone_number=number)


@registration_route.get("/user/{number}", response_model=registration.UserSummary)
def get_registered_user_by_phone(number: str, db: Session = Depends(get_db)):
    phone = (
        db.query(phone_number.PhoneNumber)
        .filter(phone_number.PhoneNumber.phone_number == number)
        .first()
    )
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found.")

    user_record = (
        db.query(user.User).filter(user.User.phone_number_id == phone.id).first()
    )
    if not user_record:
        raise HTTPException(
            status_code=404, detail="No user registered with this number."
        )

    floor_map = {
        0: "Ground Floor",
        1: "First Floor",
        2: "Second Floor",
        3: "Third Floor",
        4: "Fourth Floor",
        5: "Fifth Floor",
    }

    return {
        "id": user_record.id,
        "first_name": user_record.first_name,
        "category": user_record.category,
        "hall_name": user_record.hall_name,
        "floor": user_record.floor,
        "display_floor": floor_map.get(user_record.floor, f"Floor {user_record.floor}"),
        "bed_number": user_record.bed_number,
        "extra_beds": user_record.extra_beds or [],
        "phone_number": phone.phone_number,
    }


@registration_route.get("/users", response_model=list[registration.UserSummary])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(user.User).all()

    phone_map = {
        record.id: record.phone_number
        for record in db.query(phone_number.PhoneNumber).all()
    }

    floor_map = {
        0: "Ground Floor",
        1: "First Floor",
        2: "Second Floor",
        3: "Third Floor",
        4: "Fourth Floor",
        5: "Fifth Floor",
    }

    return [
        registration.UserSummary(
            id=user.id,
            first_name=user.first_name,
            category=user.category,
            hall_name=user.hall_name,
            floor=user.floor,
            display_floor=floor_map.get(user.floor, f"Floor {user.floor}"),
            bed_number=user.bed_number,
            extra_beds=user.extra_beds or [],
            phone_number=phone_map.get(user.phone_number_id, "Unknown"),
        )
        for user in users
    ]
