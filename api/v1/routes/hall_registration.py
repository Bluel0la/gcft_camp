from api.utils.user_registration import register_user_service, manual_register_user_service, register_phone_number_manually
from api.v1.schemas.registration import UserDisplay, UserRegistration, UserSummary, UserView
from api.v1.schemas.phone_registration import PhoneNumberRegistration, PhoneNumberView
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from api.utils.file_upload import refresh_presigned_url_if_expired
from api.v1.services.full_halls import send_hall_full_email
from api.v1.models.phone_number import PhoneNumber
from api.utils.message import send_sms_termii
from api.v1.models import phone_number, user
from api.v1.models.floor import HallFloors
from api.v1.models.user import User
from sqlalchemy.orm import Session
from api.db.database import get_db
from datetime import datetime

registration_route = APIRouter(tags=["Hall Registration"])

# Register a User's Phone Number
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

# Register a User
@registration_route.post( "/register-user/{number}",response_model=UserDisplay)
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
        number=number
    )

    # send_sms_termii(
    #    phone_number=number,
    #    name=new_user.first_name,
    #    arrival_date=new_user.arrival_date,
    #    hall=new_user.hall_name,
    #    floor=floor.floor_no,
    #    bed_no=new_user.bed_number,
    #    country=new_user.country,
    # )

    floor_record = db.query(HallFloors).filter(HallFloors.floor_id == floor.floor_id).first()

    return {
        "id": new_user.id,
        "first_name": new_user.first_name,
        "gender": new_user.gender,
        "category": new_user.category,
        "hall_name": new_user.hall_name,
        "floor": "Triple A Games are ass.....",#f"Floor {floor_record.floor_no}",
        "bed_number": new_user.bed_number,
        "extra_beds": new_user.extra_beds or [],
        "phone_number": number,
        "active_status": new_user.active_status,
        "profile_picture_url": new_user.profile_picture_url,
        "age_range": new_user.age_range,
        "marital_status": new_user.marital_status,
        "country": new_user.country,
        "state": new_user.state,
        "arrival_date": new_user.arrival_date
    }

# Register a User Manually by allocating them another's bed space
@registration_route.post("/register-user-manual/{number_manual_register}", response_model=UserDisplay)
async def register_user_manually(
    number_manual_register: str,
    number_late_comer: str,
    payload: UserRegistration = Depends(UserRegistration.as_form),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    register_phone_number_manually(phone_number=number_manual_register, db=db)

    phone = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.phone_number == number_manual_register)
        .first()
    )
    if not phone:
        raise HTTPException(404, "Phone number not found")

    existing = db.query(User).filter(User.phone_number_id == phone.id).first()
    if existing:
        raise HTTPException(409, "User already registered")

    new_user, floor = await manual_register_user_service(
        db=db, payload=payload, phone=phone, file=file, number=number_manual_register, late_comers_number=number_late_comer
    )


    return {
        "id": new_user.id,
        "first_name": new_user.first_name,
        "gender": new_user.gender,
        "category": new_user.category,
        "hall_name": new_user.hall_name,
        "floor": f"Floor {floor}",
        "bed_number": new_user.bed_number,
        "extra_beds": new_user.extra_beds or [],
        "phone_number": number_manual_register,
        "active_status": new_user.active_status,
        "profile_picture_url": new_user.profile_picture_url,
        "age_range": new_user.age_range,
        "marital_status": new_user.marital_status,
        "country": new_user.country,
        "state": new_user.state,
        "arrival_date": new_user.arrival_date,
    }

# Register a user using backup Spaces
@registration_route.post("/register-user-backup/{phone_number}", response_model=UserDisplay)


# Get a registered user by phone number
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

    profile_picture_url = refresh_presigned_url_if_expired(user_record, db)

    return {
        "id": user_record.id,
        "first_name": user_record.first_name,
        "category": user_record.category,
        "hall_name": user_record.hall_name,
        "floor": f"Floor {floor.floor_no}",
        "bed_number": user_record.bed_number,
        "extra_beds": user_record.extra_beds or [],
        "phone_number": phone.phone_number,
        "active_status": user_record.active_status,
        "profile_picture_url": profile_picture_url,
        "gender": user_record.gender,
        "children_names": user_record.names_children,
        "children_no": user_record.no_children,
        "local_assembly": user_record.local_assembly,
        "local_assembly_address": user_record.local_assembly_address,
        "Medical_issues": user_record.medical_issues,
        "status": user_record.active_status,
        "arrival_date": user_record.arrival_date,
        "state": user_record.state,
    }

# Return all users
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
            profile_picture_url=user.profile_picture_url,
            local_assembly=user.local_assembly,
            local_assembly_address=user.local_assembly_address,
            arrival_date=user.arrival_date,
            state=user.state,
            gender=user.gender
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
            profile_picture_url=user.profile_picture_url,
            local_assembly=user.local_assembly,
            local_assembly_address=user.local_assembly_address,
            arrival_date=user.arrival_date,
            state=user.state,
            gender=user.gender
        )
        for user in users
    ]
