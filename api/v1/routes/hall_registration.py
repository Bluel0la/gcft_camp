from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.schemas.hall_registration import HallCreate, HallUpdate, HallView
from api.v1.schemas.phone_registration import PhoneNumberRegistration, PhoneNumberView
from api.v1.schemas.registration import UserDisplay, UserRegistration, UserSummary, UserView
from api.v1.services.full_halls import send_hall_full_email
from api.v1.models import phone_number, user, category, hall
from api.v1.models.hall import Hall
from api.v1.models.floor import HallFloors
from api.db.database import get_db
from api.utils.bed_allocation import beds_required
from datetime import datetime
from sqlalchemy import or_

import asyncio

registration_route = APIRouter(tags=["Hall Registration"])


@registration_route.post("/register-number", response_model=PhoneNumberView)
def register_phone_number(
    payload: PhoneNumberRegistration, db: Session = Depends(get_db)
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
    "/register-user/{number}", response_model=UserDisplay
)
async def register_user(
    number: str, payload: UserRegistration, db: Session = Depends(get_db)
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
    
    # Find all eligible halls based on the user's gender
    eligible_halls = db.query(Hall).filter(Hall.gender == payload.gender).all()
    new_user = None  # Track if a user was registered

    for hall in eligible_halls:
        eligible_floors = db.query(HallFloors).filter(
            HallFloors.hall_id == hall.id,
            HallFloors.status == "not-full",
            HallFloors.age_range == payload.age_range,
            or_(
                HallFloors.categories.any(category.Category.category_name == payload.category),
                HallFloors.categories == []  # eligible if no categories assigned
                )
            ).order_by(HallFloors.floor_no).all()
        for floor in eligible_floors:
            if floor.last_assigned_bed is None or floor.last_assigned_bed == 0:
                floor.last_assigned_bed = 1
            if floor.last_assigned_bed <= floor.no_beds:
                assigned_bed = floor.last_assigned_bed
                # Calculate required beds
                beds = beds_required(payload.no_children, assigned_bed)
                # Update last_assigned_bed accordingly
                floor.last_assigned_bed += len(beds)
                if floor.last_assigned_bed > floor.no_beds:
                    floor.status = "full"
                db.commit()

                new_user = user.User(
                    first_name=payload.first_name,
                    category=payload.category,
                    hall_name=hall.hall_name,
                    floor=floor.floor_no,
                    bed_number=assigned_bed,
                    extra_beds=beds[1:] if len(beds) > 1 else [],
                    phone_number_id=phone.id,
                    gender=payload.gender,
                    age_range=payload.age_range,
                    marital_status=payload.marital_status,
                    state=payload.state,
                    country=payload.country,
                    arrival_date=payload.arrival_date,
                    no_children=payload.no_children,
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                break
        if new_user:
            break

    # If no user was registered, all eligible halls are full
    if not new_user:
        # Send notification for each eligible hall
        for hall in eligible_halls:
            await send_hall_full_email(hall, payload.category)
        raise HTTPException(
            status_code=400,
            detail="All eligible halls are full for this category and age range."
        )

    return UserDisplay(
        id=new_user.id,
        first_name=new_user.first_name,
        category=new_user.category,
        hall_name=new_user.hall_name,
        floor=new_user.floor,
        bed_number=new_user.bed_number,
        extra_beds=new_user.extra_beds or [],
        phone_number=phone.phone_number,
        gender=new_user.gender,
        age_range=new_user.age_range,
        marital_status=new_user.marital_status,
        state=new_user.state,
        country=new_user.country,
        arrival_date=new_user.arrival_date
    )


@registration_route.get("/user/{number}", response_model=UserSummary)
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

    

    return {
        "id": user_record.id,
        "first_name": user_record.first_name,
        "category": user_record.category,
        "hall_name": user_record.hall_name,
        "floor": user_record.floor,
        "display_floor": f"Floor {user_record.floor}",
        "bed_number": user_record.bed_number,
        "extra_beds": user_record.extra_beds or [],
        "phone_number": phone.phone_number,
    }


@registration_route.get("/users", response_model=list[UserSummary])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(user.User).all()

    phone_map = {
        record.id: record.phone_number
        for record in db.query(phone_number.PhoneNumber).all()
    }


    return [
        UserSummary(
            id=user.id,
            first_name=user.first_name,
            category=user.category,
            hall_name=user.hall_name,
            floor=user.floor,
            display_floor=f"Floor {user.floor}",
            bed_number=user.bed_number,
            extra_beds=user.extra_beds or [],
            phone_number=phone_map.get(user.phone_number_id, "Unknown"),
        )
        for user in users
    ]


# Change a users active status from inactive to active
@registration_route.put("/activate-user/{phone_number}", response_model=UserView)
def activate_user(phone_number: str, db: Session = Depends(get_db)):
    user_record = db.query(user.User).filter(user.User.phone == phone_number).first()
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found.")

    if user_record.active_status == "active":
        raise HTTPException(status_code=400, detail="User is already active.")

    user_record.active_status = "active"
    db.commit()
    db.refresh(user_record)

    return user_record
