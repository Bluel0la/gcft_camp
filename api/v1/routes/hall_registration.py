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
from api.utils.bed_allocation import beds_required, gender_classifier
from datetime import datetime
from sqlalchemy import or_
from api.v1.models.phone_number import PhoneNumber
from api.utils.message import send_sms

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


@registration_route.post("/register-user/{number}", response_model=UserDisplay)
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
    # Get their Gender from the classifier
    gender = gender_classifier(payload.category)
    print(gender)

    # Find all eligible halls based on the user's gender and any hall named "Jerusalem Hall"
    eligible_halls = db.query(Hall).filter(
        (Hall.gender == gender) | (Hall.hall_name == "Jerusalem Hall")
    ).order_by(Hall.hall_name).all()

    # Print eligble halls
    print("Eligible halls:", eligible_halls)
    new_user = None  # Track if a user was registered

    for hall in eligible_halls:
        eligible_floors = db.query(HallFloors).filter(
            HallFloors.hall_id == hall.id,
            HallFloors.status == "not-full",
            or_(
            HallFloors.age_ranges.contains([payload.age_range]),
            HallFloors.age_ranges == None,
            HallFloors.age_ranges == [],
            ),
            or_(
            HallFloors.categories.any(category.Category.category_name == payload.category),
            ~HallFloors.categories.any()
            )
        ).order_by(HallFloors.floor_no).all()
        for floor in eligible_floors:
            bunk_size = 2  # or fetch from floor config if variable
            if floor.last_assigned_bed is None or floor.last_assigned_bed == 0:
                floor.last_assigned_bed = 1
            if floor.counter_value is None:
                floor.counter_value = 0

            # Check if there are beds left
            total_beds = floor.no_beds * bunk_size
            assigned_count = ((floor.last_assigned_bed - 1) * bunk_size) + floor.counter_value
            if assigned_count < total_beds:
                bed_label, next_bed, next_counter = beds_required(
                    payload.no_children, floor.last_assigned_bed, floor.counter_value, bunk_size
                )
                # Assign bed and update counters
                floor.last_assigned_bed = next_bed
                floor.counter_value = next_counter
                if ((floor.last_assigned_bed - 1) * bunk_size + floor.counter_value) >= total_beds:
                    floor.status = "full"
                db.commit()

                new_user = user.User(
                    first_name=payload.first_name,
                    category=payload.category,
                    hall_name=hall.hall_name,
                    floor=floor.floor_id,
                    bed_number=bed_label,
                    extra_beds=[],
                    phone_number_id=phone.id,
                    gender=gender,
                    age_range=payload.age_range,
                    marital_status=payload.marital_status,
                    state=payload.state,
                    country=payload.country,
                    arrival_date=payload.arrival_date,
                    no_children=payload.no_children,
                    local_assembly=payload.local_assembly,
                    local_assembly_address=payload.local_assembly_address,
                    names_children=payload.names_children,
                    medical_issues=payload.medical_issues
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
    floor_record = db.query(HallFloors).filter(HallFloors.floor_id == new_user.floor).first()
    send_sms(phone_number=number, name=new_user.first_name, arrival_date=new_user.arrival_date, hall=new_user.hall_name, floor=floor_record.floor_no, bed_no=new_user.bed_number, country=new_user.country)

    return UserDisplay(
        
        id=new_user.id,
        first_name=new_user.first_name,
        category=new_user.category,
        hall_name=new_user.hall_name,
        floor=f"Floor {floor_record.floor_no}",
        bed_number=new_user.bed_number,
        extra_beds=new_user.extra_beds or [],
        phone_number=phone.phone_number,
        gender=new_user.gender,
        age_range=new_user.age_range,
        marital_status=new_user.marital_status,
        state=new_user.state,
        country=new_user.country,
        arrival_date=new_user.arrival_date,
        no_children=new_user.no_children,
        local_assembly=new_user.local_assembly,
        local_assembly_address=new_user.local_assembly_address,
        names_children=new_user.names_children,
        medical_issues=new_user.medical_issues
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
        
    floor = db.query(HallFloors).filter(HallFloors.floor_id == user_record.floor).first()

    

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
            floor=f"Floor {user.floor}",
            bed_number=user.bed_number,
            extra_beds=user.extra_beds or [],
            phone_number=phone_map.get(user.phone_number_id, "Unknown"),
        )
        for user in users
    ]


# Change a users active status from inactive to active
@registration_route.put("/activate-user/{phone_number}", response_model=UserView)
def activate_user(number: str, db: Session = Depends(get_db)):
    # Get the PhoneNumber object
    phone = (
        db.query(PhoneNumber).filter(PhoneNumber.phone_number == number).first()
    )
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
    )
