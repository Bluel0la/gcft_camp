"""
Registration Service — SOLID refactor.

Centralizes all registration logic: phone upsert, programme validation,
user persistence, and the two registration flows (attendance-only and
with-accommodation).
"""

from api.utils.bed_allocation import (
    allocate_bed,
    fetch_user_information_for_reallocation,
    update_lateuser_information,
    validate_gender,
    allocate_backup_bed,
    compute_hall_statistics,
)
from api.utils.file_upload import process_and_upload_image, delete_from_s3
from api.v1.services.full_halls import send_hall_full_email
from api.v1.models.phone_number import PhoneNumber
from api.v1.models.programme import Programme
from api.v1.models.user import User
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone, date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_programme_or_404(db: Session, programme_id: int) -> Programme:
    """Fetch a programme by ID or raise 404."""
    programme = db.query(Programme).filter(Programme.id == programme_id).first()
    if not programme:
        raise HTTPException(status_code=404, detail="Programme not found.")
    return programme


def ensure_registration_open(programme: Programme) -> None:
    """Raise 403 if the programme registration is not open."""
    if programme.registration_status != "open":
        raise HTTPException(
            status_code=403,
            detail=f"Registration for '{programme.programme_name}' is currently {programme.registration_status}.",
        )


def get_or_create_phone(db: Session, phone_number: str, is_child: bool = False) -> PhoneNumber:
    """
    Look up a PhoneNumber record; create one if it doesn't exist.

    If this is a child registration using a parent's number, mark the
    PhoneNumber as a parent number (is_parent=True).
    """
    phone = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.phone_number == phone_number)
        .first()
    )

    if phone:
        # If a child is registering with this number, flag it as parent number
        if is_child and not phone.is_parent:
            phone.is_parent = True
            db.flush()
        return phone

    # New phone number
    phone = PhoneNumber(
        phone_number=phone_number,
        is_parent=is_child,  # True if the first user on this number is a child
        time_registered=datetime.now(timezone.utc),
    )
    db.add(phone)
    db.flush()  # ensure phone.id is available
    return phone


def check_duplicate_registration(
    db: Session, phone_id: int, programme_id: int, is_child: bool
) -> None:
    """
    Prevent duplicate registrations.

    - Adults: one registration per phone per programme.
    - Children: multiple children can share a phone, so we skip the
      uniqueness check for children.
    """
    if is_child:
        return  # children share parent's phone

    existing = (
        db.query(User)
        .filter(
            User.phone_number_id == phone_id,
            User.programme_id == programme_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="This phone number is already registered for this programme.",
        )


def persist_user(
    db: Session,
    payload,
    phone: PhoneNumber,
    programme_id: int,
    registration_type: str,
    gender: str,
    image_url: str,
    object_key: str,
    hall=None,
    floor_id=None,
    beds=None,
    active_status: str = "inactive",
) -> User:
    """Create and persist a User record."""
    user = User(
        programme_id=programme_id,
        phone_number_id=phone.id,
        registration_type=registration_type,
        registration_completed=True,
        first_name=payload.first_name,
        category=payload.category,
        gender=gender,
        age_range=payload.age_range,
        marital_status=payload.marital_status,
        no_children=payload.no_children or 0,
        names_children=payload.names_children,
        country=payload.country,
        state=payload.state,
        arrival_date=payload.arrival_date,
        medical_issues=payload.medical_issues,
        local_assembly=payload.local_assembly,
        local_assembly_address=payload.local_assembly_address,
        # Accommodation (None for attendance-only)
        hall_id=hall.id if hall else None,
        floor_id=floor_id,
        bed_number=beds[0] if beds else None,
        extra_beds=beds[1:] if beds and len(beds) > 1 else [],
        # Profile
        profile_picture_url=image_url,
        object_key=object_key,
        date_presigned_url_generated=date.today(),
        active_status=active_status,
    )
    db.add(user)
    db.flush()
    return user


# ---------------------------------------------------------------------------
# Registration flows
# ---------------------------------------------------------------------------


async def register_attendance_only(
    db: Session, programme_id: int, payload, file, is_child: bool = False
):
    """
    Register a user for attendance only (no accommodation).
    Single-step: handles phone creation/lookup internally.
    """
    programme = get_programme_or_404(db, programme_id)
    ensure_registration_open(programme)

    gender = validate_gender(payload.category)
    phone = get_or_create_phone(db, payload.phone_number, is_child=is_child)
    check_duplicate_registration(db, phone.id, programme_id, is_child=is_child)

    object_key = None
    try:
        image_url, object_key = await process_and_upload_image(
            file, payload.first_name, payload.phone_number
        )

        user = persist_user(
            db=db,
            payload=payload,
            phone=phone,
            programme_id=programme_id,
            registration_type="attendance_only",
            gender=gender,
            image_url=image_url,
            object_key=object_key,
            active_status="inactive",
        )

        db.commit()
        db.refresh(user)
        return user, phone

    except HTTPException:
        db.rollback()
        if object_key:
            delete_from_s3(object_key)
        raise
    except Exception:
        db.rollback()
        if object_key:
            delete_from_s3(object_key)
        raise


async def register_with_accommodation(
    db: Session, programme_id: int, payload, file, is_child: bool = False
):
    """
    Register a user who needs accommodation (triggers bed allocation).
    Single-step: handles phone creation/lookup internally.
    """
    programme = get_programme_or_404(db, programme_id)
    ensure_registration_open(programme)

    gender = validate_gender(payload.category)
    phone = get_or_create_phone(db, payload.phone_number, is_child=is_child)
    check_duplicate_registration(db, phone.id, programme_id, is_child=is_child)

    # Allocate bed
    hall, floor, beds = allocate_bed(db, gender, payload)
    if not hall:
        # Notify admin if a hall just filled up
        if floor:
            stats = compute_hall_statistics(db, floor)
            await send_hall_full_email(
                hall=floor,
                total_beds=stats["total_beds"],
                allocated_beds=stats["all_users_count"],
            )
        raise HTTPException(
            status_code=400,
            detail="No accommodation available. Kindly report for physical allocation.",
        )

    object_key = None
    try:
        image_url, object_key = await process_and_upload_image(
            file, payload.first_name, payload.phone_number
        )

        user = persist_user(
            db=db,
            payload=payload,
            phone=phone,
            programme_id=programme_id,
            registration_type="with_accommodation",
            gender=gender,
            image_url=image_url,
            object_key=object_key,
            hall=hall,
            floor_id=floor.floor_id,
            beds=beds,
            active_status="inactive",
        )

        db.commit()
        db.refresh(user)
        return user, phone, floor

    except HTTPException:
        db.rollback()
        if object_key:
            delete_from_s3(object_key)
        raise
    except Exception:
        db.rollback()
        if object_key:
            delete_from_s3(object_key)
        raise


async def register_manual(
    db: Session, programme_id: int, payload, file,
    late_comers_number: str, is_child: bool = False
):
    """
    Manual registration: reassigns a late-comer's bed to a new registrant.
    """
    programme = get_programme_or_404(db, programme_id)
    ensure_registration_open(programme)

    gender = validate_gender(payload.category)
    phone = get_or_create_phone(db, payload.phone_number, is_child=is_child)
    check_duplicate_registration(db, phone.id, programme_id, is_child=is_child)

    children_count = payload.no_children or 0
    hall, floor_id, beds = fetch_user_information_for_reallocation(
        db, late_comers_number, children_count
    )
    if not hall:
        raise HTTPException(
            status_code=400,
            detail="No accommodation available. Kindly report for physical allocation.",
        )

    object_key = None
    try:
        image_url, object_key = await process_and_upload_image(
            file, payload.first_name, payload.phone_number
        )

        user = persist_user(
            db=db,
            payload=payload,
            phone=phone,
            programme_id=programme_id,
            registration_type="with_accommodation",
            gender=gender,
            image_url=image_url,
            object_key=object_key,
            hall=hall,
            floor_id=floor_id,
            beds=beds,
            active_status="active",
        )

        update_lateuser_information(db, late_comers_number)
        db.commit()
        db.refresh(user)
        return user, phone

    except HTTPException:
        db.rollback()
        if object_key:
            delete_from_s3(object_key)
        raise
    except Exception:
        db.rollback()
        if object_key:
            delete_from_s3(object_key)
        raise


async def register_backup(
    db: Session, programme_id: int, payload, file, is_child: bool = False
):
    """
    Backup registration using backup/child bed slots.
    """
    programme = get_programme_or_404(db, programme_id)
    ensure_registration_open(programme)

    gender = validate_gender(payload.category)
    phone = get_or_create_phone(db, payload.phone_number, is_child=is_child)
    check_duplicate_registration(db, phone.id, programme_id, is_child=is_child)

    hall, floor, beds = allocate_backup_bed(db, gender, payload)
    if not hall:
        raise HTTPException(
            status_code=400,
            detail="No backup accommodation available. Kindly report for physical allocation.",
        )

    object_key = None
    try:
        image_url, object_key = await process_and_upload_image(
            file, payload.first_name, payload.phone_number
        )

        user = persist_user(
            db=db,
            payload=payload,
            phone=phone,
            programme_id=programme_id,
            registration_type="with_accommodation",
            gender=gender,
            image_url=image_url,
            object_key=object_key,
            hall=hall,
            floor_id=floor.floor_id,
            beds=beds,
            active_status="active",
        )

        db.commit()
        db.refresh(user)
        return user, phone, floor

    except HTTPException:
        db.rollback()
        if object_key:
            delete_from_s3(object_key)
        raise
    except Exception:
        db.rollback()
        if object_key:
            delete_from_s3(object_key)
        raise
