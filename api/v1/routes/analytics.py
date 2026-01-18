from api.v1.schemas.analytics import UserCount, UsersMedicalConditions
from api.v1.models.phone_number import PhoneNumber
from api.v1.models.floor import HallFloors
from fastapi import HTTPException, status
from fastapi import APIRouter, Depends
from api.v1.models.hall import Hall
from api.v1.models.user import User
from sqlalchemy.orm import Session
from api.db.database import get_db
from sqlalchemy import func

analytics_route = APIRouter(prefix="/analytics", tags=["Analytics"])

# Endpoint to get the total number of users
@analytics_route.get("/total-users", response_model=UserCount)
def get_total_registered_users(db: Session = Depends(get_db)):
    count = db.query(User).count()
    return {"total_users": count}

# Endpoint to return the number of free spaces in each hall floor
@analytics_route.get("/{hall_name}/hall-statistics")
def get_hall_statistics(hall_name: str, db: Session = Depends(get_db)):
    # Check if the hall exists
    hall = db.query(Hall).filter(func.lower(Hall.hall_name) == hall_name.lower()).first()
    if not hall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hall not found"
        )
    
    # Get the floors in the hall
    floors = db.query(HallFloors).filter(HallFloors.hall_id == hall.id).all()
    total_beds = sum(floor.no_beds for floor in floors) * 2
    
    # Get the number of active users per floor
    for floor in floors:
        floor.active_users_count = db.query(User).filter(
            User.floor == floor.floor_id,
            User.active_status == "active"
        ).count()
    
    # Get all users per floor
    for floor in floors:
        floor.all_users_count = db.query(User).filter(
            User.floor == floor.floor_id
        ).count()
    
    all_users_count = sum(floor.all_users_count for floor in floors)
    verified_users_count = sum(floor.active_users_count for floor in floors)
    remaining_space = total_beds - all_users_count
        
    return{
        "hall_name": hall.hall_name,
        "no_floors": hall.no_floors,
        "total_beds": total_beds,
        "current_user_count": all_users_count,
        "verified_user_count": verified_users_count,
        "remaining_space": remaining_space,
        
        # Floor Specific Information
        "floors": [
            {
                "floor_no": f"Floor {floor.floor_no}",
                "no_beds": floor.no_beds,
                "active_users_count": floor.active_users_count,
                "all_users_count": floor.all_users_count,
            }
            for floor in floors
        ]
        
    }

# Endpoint to get users with medical conditions
@analytics_route.get("/users-medical-conditions", response_model=list[UsersMedicalConditions])
def get_users_with_medical_conditions(db: Session = Depends(get_db)):
    users= db.query(User).filter(
        User.medical_issues != None
    ).all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users with medical conditions found"
        )
    # Get the users phone number
    for user in users:
        phone_number = db.query(PhoneNumber).filter(
            PhoneNumber.id == user.phone_number_id).first()
    
    phone_number.phone_number
        
        
    result = [
        UsersMedicalConditions(
            user_name=user.first_name,
            phone_number=phone_number.phone_number,
            medical_condition=user.medical_issues
        )
        for user in users
    ]
    return result