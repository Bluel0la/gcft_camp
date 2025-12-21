from fastapi import HTTPException
from sqlalchemy.orm import Session
from api.v1.models.user import User
from api.utils.bed_allocation import allocate_bed
from api.utils.bed_allocation import gender_classifier
from api.utils.file_upload import upload_to_dropbox, delete_from_dropbox
from PIL import Image
import io


async def register_user_service(
    db: Session,
    payload,
    phone,
    file,
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
    unique_name = f"{payload.first_name}_{payload.local_assembly}.{ext}"
    folder_path = f"/{hall.hall_name}/Floor_{floor.floor_no}"
    dropbox_path = f"{folder_path}/{unique_name}"
    file_bytes = await file.read()

    image_url = None

    try:
        image_url = upload_to_dropbox(file_bytes,dropbox_path)

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
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user, floor

    except Exception:
        db.rollback()
        if image_url:
            delete_from_dropbox(dropbox_path)
        raise
