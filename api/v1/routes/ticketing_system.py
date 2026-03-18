from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from api.utils.file_upload import process_and_upload_image, delete_from_s3
from api.utils.bed_allocation import allocate_minister_manually
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import date, datetime, timezone
from typing import List
from sqlalchemy import or_


from api.db.database import get_db
from api.v1.models.minister import Minister, MealRecord
from api.v1.models.user import User
from api.v1.models.phone_number import PhoneNumber
from api.v1.schemas.ticketing import (
    MinisterCreate,
    MinisterOut,
    MealMarkInput,
    MealRecordOut,
    MinisterStatusOut,
)

ticketing_route = APIRouter(prefix="/ticketing", tags=["Ticketing System"])


# Endpoint to register in ministers into the ticketing system
@ticketing_route.post("/ministers/register", response_model=MinisterOut)
async def register_minister(
    minister_in: MinisterCreate = Depends(MinisterCreate.as_form),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
):
    # 1. Check for existing phone number
    if (
        db.query(Minister)
        .filter(Minister.phone_number == minister_in.phone_number)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Phone number already registered.")

    # 2. Handle File Upload
    image_url, object_key = None, None
    try:
        image_url, object_key = await process_and_upload_image(
            file, minister_in.first_name, minister_in.phone_number
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    # 3. Validate and retrieve hall/floor allocation if provided
    hall, floor = allocate_minister_manually(
        db, minister_in.hall_name, minister_in.floor_id, minister_in.bed_number
    )

    # 4. Save to Database
    try:
        # Create minister with explicitly mapped fields
        new_minister = Minister(
            phone_number=minister_in.phone_number,
            first_name=minister_in.first_name,
            last_name=minister_in.last_name,
            category=minister_in.category or "minister",
            room_number=minister_in.room_number,
            medical_issues=minister_in.medical_issues,
            local_assembly=minister_in.local_assembly,
            local_assembly_address=minister_in.local_assembly_address,
            profile_picture_url=image_url,
            object_key=object_key,
            date_presigned_url_generated=date.today(),
            hall_name=hall.hall_name if hall else None,
            floor=floor.floor_id if floor else None,
            bed_number=minister_in.bed_number if floor else None,
        )

        db.add(new_minister)

        # 5. Save to User Table as well
        phone = (
            db.query(PhoneNumber)
            .filter(PhoneNumber.phone_number == minister_in.phone_number)
            .first()
        )
        if not phone:
            phone = PhoneNumber(
                phone_number=minister_in.phone_number,
                time_registered=datetime.now(timezone.utc),
            )
            db.add(phone)
            db.flush()  # ensure phone.id is available

        # Check for existing user to avoid duplicates
        existing_user = db.query(User).filter(User.phone_number_id == phone.id).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="A user with this phone number already exists.",
            )

        new_user = User(
            phone_number_id=phone.id,
            category=minister_in.category or "minister",
            first_name=minister_in.first_name,
            gender=(
                minister_in.gender.value
                if hasattr(minister_in.gender, "value")
                else minister_in.gender
            ),
            age_range=minister_in.age_range.value,
            marital_status=minister_in.marital_status,
            country=minister_in.country,
            state=minister_in.state,
            arrival_date=minister_in.arrival_date,
            date_verified=date.today(),
            active_status="active",
            local_assembly=minister_in.local_assembly,
            local_assembly_address=minister_in.local_assembly_address,
            medical_issues=minister_in.medical_issues,
            profile_picture_url=image_url,
            object_key=object_key,
            date_presigned_url_generated=date.today(),
            hall_name=hall.hall_name if hall else None,
            floor=str(floor.floor_id) if floor else None,
            bed_number=minister_in.bed_number if floor else None,
        )
        db.add(new_user)

        db.commit()
        db.refresh(new_minister)
        return new_minister

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as e:
        db.rollback()
        if object_key:
            delete_from_s3(object_key)

        print(f"DATABASE ERROR: {e}")

        raise HTTPException(
            status_code=500,
            detail="Database save failed. Please try again or contact support.",
        )


# Endpoint to mark ministers that have gotten a meal
@ticketing_route.post(
    "/meals/mark", response_model=MealRecordOut, status_code=status.HTTP_201_CREATED
)
def mark_meal(meal_in: MealMarkInput, db: Session = Depends(get_db)):
    # 1. Search by either identifier in one go
    minister = (
        db.query(Minister)
        .filter(
            or_(
                Minister.identification_meal_number
                == meal_in.identification_meal_number,
                Minister.phone_number == meal_in.phone_number,
            )
        )
        .first()
    )

    if not minister:
        raise HTTPException(status_code=404, detail="Minister not found.")

    # 2. Logic for marking meal...
    meal_date = meal_in.meal_date or date.today()
    new_record = MealRecord(
        minister_id=minister.id, date=meal_date, meal_type=meal_in.meal_type.lower()
    )

    db.add(new_record)
    try:
        db.commit()
        db.refresh(new_record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"{minister.first_name} has already taken {meal_in.meal_type} for today.",
        )
    return new_record


# Endpoint to check if a minister has gotten a meal
@ticketing_route.get("/meals/status/{phone_number}", response_model=MinisterStatusOut)
def get_meal_status(phone_number: str, db: Session = Depends(get_db)):
    minister = db.query(Minister).filter(Minister.phone_number == phone_number).first()
    if not minister:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Minister not found."
        )

    records = (
        db.query(MealRecord)
        .filter(MealRecord.minister_id == minister.id)
        .order_by(MealRecord.date)
        .all()
    )
    meal_dates = [record.date for record in records]

    return MinisterStatusOut(
        minister=minister, total_meals_taken=len(records), meal_dates=meal_dates
    )


# Endpoint to fetch ministers that haven't had a meal
@ticketing_route.get("/meals/pending", response_model=List[MinisterOut])
def get_pending_ministers(meal_type: str, db: Session = Depends(get_db)):
    """
    Fetch ministers who haven't had a SPECIFIC meal today.
    Example: /meals/pending?meal_type=lunch
    """
    today = date.today()

    pending_ministers = (
        db.query(Minister)
        .filter(
            ~Minister.meal_records.any(
                (MealRecord.date == today) & (MealRecord.meal_type == meal_type.lower())
            )
        )
        .all()
    )

    return pending_ministers
