from api.utils.bed_allocation import allocate_bed, fetch_user_information_for_reallocation, update_lateuser_information
from api.utils.file_upload import process_and_upload_image, delete_from_s3
from api.utils.bed_allocation import validate_gender, allocate_backup_bed
from api.utils.bed_allocation import compute_hall_statistics
from api.v1.services.full_halls import send_hall_full_email
from api.v1.models.phone_number import PhoneNumber
from api.v1.models.user import User
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime


def persist_user(db: Session, payload, phone, hall, floor_id, beds, gender: str, image_url: str, object_key: str, active_status: str | None = None ):
    user = User(
        first_name=payload.first_name,
        category=payload.category,
        hall_name=hall.hall_name,
        floor=floor_id,
        bed_number=beds[0],
        extra_beds=beds[1:],
        phone_number_id=phone.id,
        gender=gender,
        age_range=payload.age_range,
        marital_status=payload.marital_status,
        state=payload.state,
        country=payload.country,
        arrival_date=payload.arrival_date,
        no_children=payload.no_children or 0,
        local_assembly=payload.local_assembly,
        local_assembly_address=payload.local_assembly_address,
        names_children=payload.names_children,
        medical_issues=payload.medical_issues,
        profile_picture_url=image_url,
        object_key=object_key,
        date_presigned_url_generated=datetime.utcnow(),
        active_status=active_status,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


async def register_user_service(db: Session, payload, phone, file, number):
    gender = validate_gender(payload.category)

    hall, floor, beds = allocate_bed(db, gender, payload)
    if not hall and floor:
        stats = compute_hall_statistics(db, floor)
        await send_hall_full_email(
            hall=floor,
            total_beds=stats["total_beds"],
            allocated_beds=stats["all_users_count"],
        )

        raise HTTPException(
            status_code=400,
            detail="All eligible halls are full for this category and age range.",
        )

    object_key = None
    try:
        image_url, object_key = await process_and_upload_image(
            file, payload.first_name, number
        )

        user = persist_user(
            db=db,
            payload=payload,
            phone=phone,
            hall=hall,
            floor_id=floor.floor_id,
            beds=beds,
            gender=gender,
            image_url=image_url,
            object_key=object_key,
        )

        return user, floor

    except Exception:
        db.rollback()
        if object_key:
            delete_from_s3(object_key)
        raise


async def manual_register_user_service(
    db: Session,
    payload,
    phone,
    file,
    number,
    late_comers_number: str,
):
    gender = validate_gender(payload.category)
    payload.no_children = payload.no_children or 0

    hall, floor, beds = fetch_user_information_for_reallocation(
        db, late_comers_number, payload.no_children
    )

    if not hall:
        raise HTTPException(
            status_code=400,
            detail="All eligible halls are full for this category and age range.",
        )

    object_key = None
    try:
        image_url, object_key = await process_and_upload_image(
            file, payload.first_name, number
        )

        user = persist_user(
            db=db,
            payload=payload,
            phone=phone,
            hall=hall,
            floor_id=floor,
            beds=beds,
            gender=gender,
            image_url=image_url,
            object_key=object_key,
            active_status="active",
        )

        update_lateuser_information(db, late_comers_number)
        return user, floor

    except Exception:
        db.rollback()
        if object_key:
            delete_from_s3(object_key)
        raise

async def backup_user_service(
    db: Session,
    payload,
    phone, file, number
):
    gender = validate_gender(payload.category)
    hall, floor, beds = allocate_backup_bed(db, gender, payload)
    if not hall:
        raise HTTPException(
            status_code=400,
            detail="All eligible halls are full for backup allocation.",
        )
    object_key = None
    try:
        image_url, object_key = await process_and_upload_image(
            file, payload.first_name, number
        )

        user = persist_user(
            db=db,
            payload=payload,
            phone=phone,
            hall=hall,
            floor_id=floor.floor_id,
            beds=beds,
            gender=gender,
            image_url=image_url,
            object_key=object_key,
            active_status="active"
        )

        return user, floor

    except Exception:
        db.rollback()
        if object_key:
            delete_from_s3(object_key)
        raise


def register_phone_number_manually(phone_number, db):
    phone = PhoneNumber(
        phone_number=phone_number,
        time_registered=datetime.utcnow(),
    )

    db.add(phone)
    db.commit()
    db.refresh(phone)
    return phone
