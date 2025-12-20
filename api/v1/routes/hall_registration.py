from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from api.v1.schemas.hall_registration import HallCreate, HallUpdate, HallView
from api.v1.schemas.phone_registration import PhoneNumberRegistration, PhoneNumberView
from api.v1.schemas.registration import (
    UserDisplay,
    UserRegistration,
    UserSummary,
    UserView,
)
from api.v1.services.full_halls import send_hall_full_email
from api.v1.models import phone_number, user, category, hall
from api.v1.models.hall import Hall
from api.v1.models.floor import HallFloors
from api.db.database import get_db
from datetime import datetime
from api.v1.models.phone_number import PhoneNumber
from api.utils.message import send_sms_termii, send_sms_termii_whatsapp
from dropbox.exceptions import ApiError
from api.utils.registration import register_user_service
from api.v1.models.user import User

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
        time_registered=datetime.utcnow(),
    )

    db.add(phone)
    db.commit()
    db.refresh(phone)
    return phone


@registration_route.post(
    "/register-user/{number}",
    response_model=UserDisplay,
)
async def register_user(
    number: str,
    payload: UserRegistration = Depends(UserRegistration.as_form),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    phone = db.query(PhoneNumber).filter(PhoneNumber.phone_number == number).first()
    if not phone:
        raise HTTPException(404, "Phone number not found")

    existing = db.query(User).filter(User.phone_number_id == phone.id).first()
    if existing:
        raise HTTPException(409, "User already registered")

    new_user, floor = await register_user_service(
        db=db,
        payload=payload,
        phone=phone,
        file=file,
    )

    #await send_sms_termii(
    #    phone_number=number,
    #    name=new_user.first_name,
    #    arrival_date=new_user.arrival_date,
    #    hall=new_user.hall_name,
    #    floor=floor.floor_no,
    #    bed_no=new_user.bed_number,
    #    country=new_user.country,
    #)
    
    floor_record = db.query(HallFloors).filter(HallFloors.floor_id == floor.floor_id).first()
    

    return {
        "id": new_user.id,
        "name": new_user.first_name,
        "category": new_user.category,
        "hall_name": new_user.hall_name,
        "floor": f"Floor {floor_record.floor_no}",
        "bed_number": new_user.bed_number,
        "extra_beds": new_user.extra_beds or [],
        "phone_number": number,
        "status": new_user.active_status,
        "profile_picture_url": new_user.profile_picture_url,
    }


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

    floor = (
        db.query(HallFloors).filter(HallFloors.floor_id == user_record.floor).first()
    )

    return {
        "id": user_record.id,
        "first_name": user_record.first_name,
        "category": user_record.category,
        "hall_name": user_record.hall_name,
        "floor": f"Floor {floor.floor_no}",
        "display_floor": f"Floor {user_record.floor}",
        "bed_number": user_record.bed_number,
        "extra_beds": user_record.extra_beds or [],
        "phone_number": phone.phone_number,
        "status": user_record.active_status,
        "profile_picture_url": user_record.profile_picture_url,
        "gender": user_record.gender,
        "children_names": user_record.names_children,
        "children_no": user_record.no_children,
        "local_assembly": user_record.local_assembly,
        "local_assembly_address": user_record.local_assembly_address,
        "Medical_issues": user_record.medical_issues,
        "status": user_record.active_status
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
            floor=(
                f"Floor {db.query(HallFloors).filter(HallFloors.floor_id == user.floor).first().floor_no}"
                if user.floor
                else None
            ),
            bed_number=user.bed_number,
            extra_beds=user.extra_beds or [],
            phone_number=phone_map.get(user.phone_number_id, "Unknown"),
            active_status=user.active_status,
            profile_picture_url=user.profile_picture_url
        )
        for user in users
    ]


# Change a users active status from inactive to active
@registration_route.put("/activate-user/{phone_number}", response_model=UserView)
def activate_user(number: str, db: Session = Depends(get_db)):
    # Get the PhoneNumber object
    phone = db.query(PhoneNumber).filter(PhoneNumber.phone_number == number).first()
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found.")

    # Get the user by phone_number_id
    user_record = (
        db.query(user.User).filter(user.User.phone_number_id == phone.id).first()
    )
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found.")

    # Check the user's current status
    if user_record.active_status == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already Enrolled"
        )
    user_record.active_status = "active"
    db.commit()
    db.refresh(user_record)
    floor_record = (
        db.query(HallFloors).filter(HallFloors.floor_id == user_record.floor).first()
    )
    floor_no = floor_record.floor_no if floor_record else None
    return UserView(
        id=user_record.id,
        first_name=user_record.first_name,
        category=user_record.category,
        hall_name=user_record.hall_name,
        floor=f"Floor {floor_no}" if floor_no else None,
        bed_number=user_record.bed_number,
        extra_beds=user_record.extra_beds or [],
        phone_number=phone.phone_number,
        gender=user_record.gender,
        age_range=user_record.age_range,
        marital_status=user_record.marital_status,
        state=user_record.state,
        country=user_record.country,
        arrival_date=user_record.arrival_date,
        no_children=user_record.no_children,
        local_assembly=user_record.local_assembly,
        local_assembly_address=user_record.local_assembly_address,
        names_children=user_record.names_children,
        medical_issues=user_record.medical_issues,
        active_status=user_record.active_status,
        profile_picture_url=user_record.profile_picture_url
    )


# return all active users
@registration_route.get("/active-users", response_model=list[UserSummary])
def get_active_users(db: Session = Depends(get_db)):
    users = db.query(user.User).filter(user.User.active_status == "active").all()

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
            floor=(
                f"Floor {db.query(HallFloors).filter(HallFloors.floor_id == user.floor).first().floor_no}"
                if user.floor
                else None
            ),
            bed_number=user.bed_number,
            extra_beds=user.extra_beds or [],
            phone_number=phone_map.get(user.phone_number_id, "Unknown"),
            active_status=user.active_status,
            profile_picture_url=user.profile_picture_url
        )
        for user in users
    ]

# Endpoint to manually allocate a bed to a user
# @registration_route.post("/allocate-bed/{user_id}", response_model=UserView)
# def allocate_bed_to_user(user_id:int, db: Session = Depends(get_db)):
