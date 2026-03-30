"""Analytics endpoints — programme-scoped, N+1 fixed."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.db.database import get_db
from api.v1.models.user import User
from api.v1.models.hall import Hall
from api.v1.models.floor import HallFloors
from api.v1.models.phone_number import PhoneNumber
from api.v1.schemas.analytics import UserCount, UsersMedicalConditions

analytics_route = APIRouter(prefix="/analytics", tags=["Analytics"])


@analytics_route.get("/total-users", response_model=UserCount)
def get_total_registered_users(
    programme_id: int = None, db: Session = Depends(get_db)
):
    """
    Get total registered users.

    Optional query param `programme_id` scopes the count to a programme.
    """
    query = db.query(func.count(User.id))
    if programme_id:
        query = query.filter(User.programme_id == programme_id)
    count = query.scalar()
    return {"total_users": count}


@analytics_route.get("/{hall_name}/hall-statistics")
def get_hall_statistics(
    hall_name: str,
    programme_id: int = None,
    db: Session = Depends(get_db),
):
    """
    Get bed statistics for a hall.

    Uses a single grouped query per hall instead of N+1 queries per floor.
    Optional query param `programme_id` scopes user counts.
    """
    hall = (
        db.query(Hall)
        .filter(func.lower(Hall.hall_name) == hall_name.lower())
        .first()
    )
    if not hall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hall not found."
        )

    floors = (
        db.query(HallFloors)
        .filter(HallFloors.hall_id == hall.id)
        .order_by(HallFloors.floor_no)
        .all()
    )

    total_beds = sum(floor.no_beds for floor in floors) * 2  # bunk beds
    floor_ids = [f.floor_id for f in floors]

    if not floor_ids:
        return {
            "hall_name": hall.hall_name,
            "no_floors": hall.no_floors,
            "total_beds": 0,
            "current_user_count": 0,
            "verified_user_count": 0,
            "remaining_space": 0,
            "floors": [],
        }

    # Single grouped query: count all users and active users per floor
    user_filter = User.floor_id.in_(floor_ids)
    if programme_id:
        user_filter = (User.floor_id.in_(floor_ids)) & (User.programme_id == programme_id)

    floor_stats = (
        db.query(
            User.floor_id,
            func.count(User.id).label("all_count"),
            func.count(
                func.nullif(User.active_status != "active", True)
            ).label("active_count"),
        )
        .filter(user_filter)
        .group_by(User.floor_id)
        .all()
    )

    stats_map = {
        row.floor_id: {"all": row.all_count, "active": row.active_count}
        for row in floor_stats
    }

    all_users_count = sum(s["all"] for s in stats_map.values())
    verified_users_count = sum(s["active"] for s in stats_map.values())
    remaining_space = total_beds - all_users_count

    return {
        "hall_name": hall.hall_name,
        "no_floors": hall.no_floors,
        "total_beds": total_beds,
        "current_user_count": all_users_count,
        "verified_user_count": verified_users_count,
        "remaining_space": remaining_space,
        "floors": [
            {
                "floor_no": f"Floor {floor.floor_no}",
                "no_beds": floor.no_beds,
                "active_users_count": stats_map.get(floor.floor_id, {}).get("active", 0),
                "all_users_count": stats_map.get(floor.floor_id, {}).get("all", 0),
            }
            for floor in floors
        ],
    }


@analytics_route.get(
    "/users-medical-conditions", response_model=list[UsersMedicalConditions]
)
def get_users_with_medical_conditions(
    programme_id: int = None, db: Session = Depends(get_db)
):
    """Get users with medical conditions. Optionally scoped to a programme."""
    query = (
        db.query(User, PhoneNumber)
        .outerjoin(PhoneNumber, PhoneNumber.id == User.phone_number_id)
        .filter(
            User.medical_issues.isnot(None),
            User.medical_issues != "",
        )
    )

    if programme_id:
        query = query.filter(User.programme_id == programme_id)

    rows = query.all()

    if not rows:
        return []

    return [
        UsersMedicalConditions(
            user_name=user.first_name,
            phone_number=(phone.phone_number if phone else "Unknown"),
            medical_condition=user.medical_issues,
        )
        for user, phone in rows
    ]


@analytics_route.get("/{programme_id}/registrations-by-type")
def get_registrations_by_type(programme_id: int, db: Session = Depends(get_db)):
    """Breakdown of registrations by type for a programme."""
    results = (
        db.query(
            User.registration_type,
            func.count(User.id).label("count"),
        )
        .filter(User.programme_id == programme_id)
        .group_by(User.registration_type)
        .all()
    )

    breakdown = {row.registration_type: row.count for row in results}

    total = sum(breakdown.values())
    return {
        "programme_id": programme_id,
        "total_registrations": total,
        "attendance_only": breakdown.get("attendance_only", 0),
        "with_accommodation": breakdown.get("with_accommodation", 0),
    }
