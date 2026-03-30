"""
Registration endpoints — programme-scoped, single-step.

All registration endpoints are under /programmes/{programme_id}/...
Lookup and listing endpoints remain at the top level.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.models.user import User
from api.v1.models.phone_number import PhoneNumber
from api.v1.models.floor import HallFloors
from api.v1.models.hall import Hall
from api.v1.schemas.registration import (
    UserDisplay,
    UserRegistration,
    UserSummary,
    UserView,
)
from api.v1.services.registration_service import (
    register_attendance_only,
    register_with_accommodation,
    register_manual,
    register_backup,
)
from api.utils.file_upload import refresh_presigned_url_if_expired
from api.utils.message import send_sms_termii, send_sms_termii_attendance_only

registration_route = APIRouter(tags=["Registration"])


# ---------------------------------------------------------------------------
# Helper to build display response
# ---------------------------------------------------------------------------

def _build_user_display(user: User, phone_number: str, floor=None) -> dict:
    """Build a standardised UserDisplay dict from a User ORM object."""
    floor_label = None
    if floor is not None:
        floor_no = floor.floor_no if hasattr(floor, "floor_no") else floor
        floor_label = f"Floor {floor_no}"

    hall_name = None
    if user.hall:
        hall_name = user.hall.hall_name

    return {
        "id": user.id,
        "first_name": user.first_name,
        "gender": user.gender,
        "category": user.category,
        "registration_type": user.registration_type,
        "registration_completed": user.registration_completed,
        "hall_name": hall_name,
        "floor": floor_label,
        "bed_number": user.bed_number,
        "extra_beds": user.extra_beds or [],
        "phone_number": phone_number,
        "active_status": user.active_status,
        "profile_picture_url": user.profile_picture_url,
        "age_range": user.age_range,
        "marital_status": user.marital_status,
        "country": user.country,
        "state": user.state,
        "arrival_date": user.arrival_date,
    }


# ---------------------------------------------------------------------------
# Registration endpoints (programme-scoped)
# ---------------------------------------------------------------------------


@registration_route.post(
    "/programmes/{programme_id}/register-attendance",
    response_model=UserDisplay,
)
async def register_attendance_endpoint(
    programme_id: int,
    payload: UserRegistration = Depends(UserRegistration.as_form),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Register for attendance only (own accommodation)."""
    is_child = payload.age_range.value == "10-17"
    user, phone = await register_attendance_only(
        db=db, programme_id=programme_id, payload=payload, file=file, is_child=is_child
    )

    send_sms_termii_attendance_only(
        phone_number=payload.phone_number,
        name=user.first_name,
        arrival_date=str(user.arrival_date),
        country=user.country,
    )

    return _build_user_display(user, payload.phone_number)


@registration_route.post(
    "/programmes/{programme_id}/register-with-accommodation",
    response_model=UserDisplay,
)
async def register_with_accommodation_endpoint(
    programme_id: int,
    payload: UserRegistration = Depends(UserRegistration.as_form),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Register with accommodation (triggers bed allocation)."""
    is_child = payload.age_range.value == "10-17"
    user, phone, floor = await register_with_accommodation(
        db=db, programme_id=programme_id, payload=payload, file=file, is_child=is_child
    )

    send_sms_termii(
        phone_number=payload.phone_number,
        name=user.first_name,
        arrival_date=str(user.arrival_date),
        hall=user.hall.hall_name if user.hall else "N/A",
        floor=floor.floor_no,
        bed_no=user.bed_number,
        country=user.country,
    )

    return _build_user_display(user, payload.phone_number, floor)


@registration_route.post(
    "/programmes/{programme_id}/register-manual",
    response_model=UserDisplay,
)
async def register_manual_endpoint(
    programme_id: int,
    late_comers_number: str,
    payload: UserRegistration = Depends(UserRegistration.as_form),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Manually register by reassigning a late-comer's bed."""
    is_child = payload.age_range.value == "10-17"
    user, phone = await register_manual(
        db=db,
        programme_id=programme_id,
        payload=payload,
        file=file,
        late_comers_number=late_comers_number,
        is_child=is_child,
    )

    return _build_user_display(user, payload.phone_number)


@registration_route.post(
    "/programmes/{programme_id}/register-backup",
    response_model=UserDisplay,
)
async def register_backup_endpoint(
    programme_id: int,
    payload: UserRegistration = Depends(UserRegistration.as_form),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Register using backup/child bed slots."""
    is_child = payload.age_range.value == "10-17"
    user, phone, floor = await register_backup(
        db=db, programme_id=programme_id, payload=payload, file=file, is_child=is_child
    )

    return _build_user_display(user, payload.phone_number, floor)


# ---------------------------------------------------------------------------
# Lookup endpoints
# ---------------------------------------------------------------------------


@registration_route.get("/registrations/{phone_number}", response_model=UserSummary)
def get_registered_user_by_phone(phone_number: str, db: Session = Depends(get_db)):
    """Look up a registered user by phone number."""
    phone = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.phone_number == phone_number)
        .first()
    )
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found.")

    user_record = (
        db.query(User).filter(User.phone_number_id == phone.id).first()
    )
    if not user_record:
        raise HTTPException(
            status_code=404, detail="No user registered with this number."
        )

    # Refresh profile picture URL if expired
    profile_picture_url = refresh_presigned_url_if_expired(user_record, db)

    floor_label = None
    if user_record.floor_id:
        floor = (
            db.query(HallFloors)
            .filter(HallFloors.floor_id == user_record.floor_id)
            .first()
        )
        if floor:
            floor_label = f"Floor {floor.floor_no}"

    hall_name = None
    if user_record.hall:
        hall_name = user_record.hall.hall_name

    return UserSummary(
        id=user_record.id,
        first_name=user_record.first_name,
        category=user_record.category,
        registration_type=user_record.registration_type,
        registration_completed=user_record.registration_completed,
        hall_name=hall_name,
        floor=floor_label,
        bed_number=user_record.bed_number,
        extra_beds=user_record.extra_beds or [],
        phone_number=phone.phone_number,
        active_status=user_record.active_status,
        profile_picture_url=profile_picture_url,
        gender=user_record.gender,
        local_assembly=user_record.local_assembly,
        local_assembly_address=user_record.local_assembly_address,
        medical_issues=user_record.medical_issues,
        arrival_date=user_record.arrival_date,
        state=user_record.state,
    )


@registration_route.get(
    "/programmes/{programme_id}/registrations", response_model=list[UserSummary]
)
def get_programme_registrations(
    programme_id: int,
    status: str = None,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    List registrations for a programme.

    Optional query param `status` filters by active_status (e.g. ?status=active).
    """
    query = (
        db.query(User)
        .filter(User.programme_id == programme_id)
    )

    if status:
        query = query.filter(User.active_status == status)

    users = query.order_by(User.id).offset(skip).limit(limit).all()

    # Batch-load phone numbers and floors to avoid N+1
    phone_ids = [u.phone_number_id for u in users if u.phone_number_id]
    floor_ids = [u.floor_id for u in users if u.floor_id]

    phone_map = {
        p.id: p.phone_number
        for p in db.query(PhoneNumber).filter(PhoneNumber.id.in_(phone_ids)).all()
    } if phone_ids else {}

    floor_map = {
        f.floor_id: f.floor_no
        for f in db.query(HallFloors).filter(HallFloors.floor_id.in_(floor_ids)).all()
    } if floor_ids else {}

    hall_ids = [u.hall_id for u in users if u.hall_id]
    hall_map = {
        h.id: h.hall_name
        for h in db.query(Hall).filter(Hall.id.in_(hall_ids)).all()
    } if hall_ids else {}

    return [
        UserSummary(
            id=u.id,
            first_name=u.first_name,
            category=u.category,
            registration_type=u.registration_type,
            registration_completed=u.registration_completed,
            hall_name=hall_map.get(u.hall_id),
            floor=(
                f"Floor {floor_map[u.floor_id]}"
                if u.floor_id and u.floor_id in floor_map
                else None
            ),
            bed_number=u.bed_number,
            extra_beds=u.extra_beds or [],
            phone_number=phone_map.get(u.phone_number_id, "Unknown"),
            active_status=u.active_status,
            profile_picture_url=u.profile_picture_url,
            local_assembly=u.local_assembly,
            local_assembly_address=u.local_assembly_address,
            arrival_date=u.arrival_date,
            state=u.state,
            gender=u.gender,
        )
        for u in users
    ]


# ---------------------------------------------------------------------------
# Status management
# ---------------------------------------------------------------------------


@registration_route.put(
    "/registrations/{phone_number}/activate", response_model=UserView
)
def activate_user(phone_number: str, db: Session = Depends(get_db)):
    """Activate a user (change status from inactive → active)."""
    phone = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.phone_number == phone_number)
        .first()
    )
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found.")

    user_record = (
        db.query(User).filter(User.phone_number_id == phone.id).first()
    )
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found.")

    if user_record.active_status == "active":
        raise HTTPException(status_code=400, detail="User is already active.")

    user_record.active_status = "active"
    db.commit()
    db.refresh(user_record)

    floor_label = None
    if user_record.floor_id:
        floor_record = (
            db.query(HallFloors)
            .filter(HallFloors.floor_id == user_record.floor_id)
            .first()
        )
        if floor_record:
            floor_label = f"Floor {floor_record.floor_no}"

    hall_name = None
    if user_record.hall:
        hall_name = user_record.hall.hall_name

    return UserView(
        id=user_record.id,
        first_name=user_record.first_name,
        gender=user_record.gender,
        category=user_record.category,
        registration_type=user_record.registration_type,
        registration_completed=user_record.registration_completed,
        hall_name=hall_name,
        floor=floor_label,
        bed_number=user_record.bed_number,
        extra_beds=user_record.extra_beds or [],
        phone_number=phone.phone_number,
        active_status=user_record.active_status,
        profile_picture_url=user_record.profile_picture_url,
        age_range=user_record.age_range,
        marital_status=user_record.marital_status,
        country=user_record.country,
        state=user_record.state,
        arrival_date=user_record.arrival_date,
        no_children=user_record.no_children,
        names_children=user_record.names_children,
        medical_issues=user_record.medical_issues,
        local_assembly=user_record.local_assembly,
        local_assembly_address=user_record.local_assembly_address,
    )
