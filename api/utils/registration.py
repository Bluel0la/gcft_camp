from fastapi import HTTPException
from sqlalchemy.orm import Session
from api.v1.models.user import User
from api.utils.bed_allocation import allocate_bed, fetch_user_information_for_reallocation, update_lateuser_information
from api.utils.bed_allocation import gender_classifier
from api.utils.file_upload import upload_to_s3, delete_from_s3, clean_image
import uuid
from datetime import datetime
from api.v1.models.phone_number import PhoneNumber

async def register_user_service(
    db: Session,
    payload,
    phone,
    file,
    number
):
    gender = gender_classifier(payload.category)
    if gender not in {"male", "female"}:
        raise HTTPException(400, "Invalid gender classification")

    hall, floor, beds = allocate_bed(db, gender, payload)

    if not hall:
        raise HTTPException(
            status_code=400,
            detail="All eligible halls are full for this category and age range.",
        )

    ext = file.filename.split(".")[-1]
    safe_name=payload.first_name.lower().replace(" ", "_")
    unique_name = f"{safe_name}_{uuid.uuid4().hex}.{ext}"
    folder_path = f"users/{number}"
    object_key = f"{folder_path}/{unique_name}"
    file_bytes = await file.read()

    image_url = None

    processed_bytes, content_type = clean_image(
        file_bytes=file_bytes,
        target_size=(512, 512), crop=True
    )

    try:
        image_url = upload_to_s3(
            file_bytes=processed_bytes,
            object_key=object_key,
            content_type=content_type,
        )

        new_user = User(
            first_name=payload.first_name,
            category=payload.category,
            hall_name=hall.hall_name,
            floor=floor.floor_id,
            bed_number=beds[0],
            extra_beds=beds[1:],
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
            medical_issues=payload.medical_issues,
            profile_picture_url=image_url,
            object_key=object_key,
            date_presigned_url_generated=datetime.utcnow()
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user, floor

    except Exception:
        db.rollback()
        if image_url:
            delete_from_s3(object_key)
        raise


async def manual_register_user_service(db: Session, payload, phone, file, number, late_comers_number: str):
    gender = gender_classifier(payload.category)
    if gender not in {"male", "female"}:
        raise HTTPException(400, "Invalid gender classification")

    no_children = payload.no_children if payload.no_children is not None else 0

    hall, floor, beds = fetch_user_information_for_reallocation(db, late_comers_number, no_children)

    if not hall:
        raise HTTPException(
            status_code=400,
            detail="All eligible halls are full for this category and age range.",
        )

    ext = file.filename.split(".")[-1]
    safe_name = payload.first_name.lower().replace(" ", "_")
    unique_name = f"{safe_name}_{uuid.uuid4().hex}.{ext}"
    folder_path = f"users/{number}"
    object_key = f"{folder_path}/{unique_name}"
    file_bytes = await file.read()

    image_url = None

    processed_bytes, content_type = clean_image(
        file_bytes=file_bytes, target_size=(512, 512), crop=True
    )

    try:
        image_url = upload_to_s3(
            file_bytes=processed_bytes,
            object_key=object_key,
            content_type=content_type,
        )

        new_user = User(
            first_name=payload.first_name,
            category=payload.category,
            hall_name=hall,
            floor=floor,
            bed_number=beds[0],
            extra_beds=beds[1:],
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
            medical_issues=payload.medical_issues,
            profile_picture_url=image_url,
            object_key=object_key,
            date_presigned_url_generated=datetime.utcnow(),
            active_status="active"
        )

        update_lateuser_information(db, late_comers_number)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user, floor

    except Exception:
        db.rollback()
        if image_url:
            delete_from_s3(object_key)
        raise


def register_phone_number_manually(
    phone_number, db
):
    phone = PhoneNumber(
        phone_number=phone_number,
        time_registered=datetime.utcnow(),
    )

    db.add(phone)
    db.commit()
    db.refresh(phone)
    return phone
