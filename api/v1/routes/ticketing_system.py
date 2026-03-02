from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from api.utils.file_upload import process_and_upload_image, delete_from_s3
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date
from typing import List
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError


from api.db.database import get_db
from api.v1.models.minister import Minister, MealRecord
from api.v1.schemas.ticketing import (
    MinisterCreate, MinisterOut, MealMarkInput, MealRecordOut, MinisterStatusOut
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

    # 3. Save to Database
    try:
        new_minister = Minister(**minister_in.model_dump())
        new_minister.profile_picture_url = image_url
        new_minister.object_key = object_key
        new_minister.date_presigned_url_generated = date.today()

        db.add(new_minister)
        db.commit()
        db.refresh(new_minister)
        return new_minister

    except Exception as e:
        db.rollback()
        if object_key:
            # IMPORTANT: Added await here
            delete_from_s3(object_key)

        # Log the actual error to your terminal so you can see why it failed!
        print(f"DATABASE ERROR: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"Database save failed: {str(e)}",  # Reveal error temporarily to debug
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
    meal_date = meal_in.date or date.today()
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Minister not found."
        )

    records = db.query(MealRecord).filter(MealRecord.minister_id == minister.id).order_by(MealRecord.date).all()
    meal_dates = [record.date for record in records]

    return MinisterStatusOut(
        minister=minister,
        total_meals_taken=len(records),
        meal_dates=meal_dates
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
