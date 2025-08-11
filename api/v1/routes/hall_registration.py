from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.schemas import phone_registration, registration, category_registration, hall_registration
from api.v1.models import phone_number, user, category, hall
from api.db.database import get_db
from datetime import datetime

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
def register_user(
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

    # Step 4: Find next available bed
    floor_allocation = None
    next_bed = None
    for record in category_records:
        assigned_beds = (
            db.query(user.User.bed_number)
            .filter(
                user.User.category == record.category_name,
                user.User.hall_name == record.hall_name,
                user.User.floor == record.floor_allocated,
            )
            .order_by(user.User.bed_number.asc())
            .all()
        )
        assigned_bed_numbers = [b[0] for b in assigned_beds]
        for i in range(1, int(record.no_beds) + 1):
            if i not in assigned_bed_numbers:
                next_bed = i
                floor_allocation = record
                break
        if floor_allocation:
            break

    if not floor_allocation or not next_bed:
        raise HTTPException(
            status_code=400,
            detail="No available beds for this category allocation.",
        )

    # Step 5: Register user
    new_user = user.User(
        **payload.dict(exclude={"hall_name", "floor", "bed_number", "phone_number_id"}),
        phone_number_id=phone.id,
        hall_name=floor_allocation.hall_name,
        floor=floor_allocation.floor_allocated,
        bed_number=next_bed,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

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

    return{
        "id": user_record.id,
        "first_name": user_record.first_name,
        "category": user_record.category,
        "hall_name": user_record.hall_name,
        "floor": user_record.floor,
        "display_floor": floor_map.get(user_record.floor, f"Floor {user_record.floor}"),
        "bed_number": user_record.bed_number,
        "phone_number": phone.phone_number,
    }


@registration_route.get("/users", response_model=list[registration.UserSummary])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(user.User).all()

    phone_map = {
        record.id: record.phone_number
        for record in db.query(phone_number.PhoneNumber).all()
    }

    return [
        registration.UserSummary(
            id=user.id,
            first_name=user.first_name,
            category=user.category,
            hall_name=user.hall_name,
            floor=user.floor,
            display_floor=(
                {
                    0: "Ground Floor",
                    1: "First Floor",
                    2: "Second Floor",
                    3: "Third Floor",
                    4: "Fourth Floor",
                    5: "Fifth Floor",
                }.get(user.floor, f"Floor {user.floor}")
            ),
            bed_number=user.bed_number,
            phone_number=phone_map.get(user.phone_number_id, "Unknown"),
        )
        for user in users
    ]
