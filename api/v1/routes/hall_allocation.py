from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.schemas import hall_registration
from api.v1.models import hall as hall_model
from api.db.database import get_db
from api.utils.bed_allocation import floor_create_logic
from api.v1.schemas.floor_management import FloorUpdateSchema, FloorViewSchema

hall_route = APIRouter(prefix="/hall", tags=["Hall Management"])


import uuid
from api.v1.models.floor import HallFloors  # Make sure this import is present


@hall_route.post("/", response_model=hall_registration.HallView)
def create_hall(payload: hall_registration.HallCreate, db: Session = Depends(get_db)):
    existing = db.query(hall_model.Hall).filter_by(hall_name=payload.hall_name).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="Hall with this name already exists."
        )

    new_hall = hall_model.Hall(**payload.dict())
    db.add(new_hall)
    db.commit()
    db.refresh(new_hall)

    # Create the corresponding floors for the hall based on the number of floors specified
    for floor_no in range(1, payload.no_floors + 1):
        floor_data = floor_create_logic(
            floor_no=floor_no,
            hall_id=new_hall.id,
            no_beds=0,  # or distribute new_hall.no_beds as needed
        )
        floor = HallFloors(
            floor_id=uuid.uuid4(),
            floor_no=floor_data.floor_no,
            hall_id=floor_data.hall_id,
            no_beds=floor_data.no_beds,
            status="not-full",
        )
        db.add(floor)
    db.commit()

    return new_hall


@hall_route.get("/", response_model=list[hall_registration.HallView])
def get_all_halls(
    db: Session = Depends(get_db)
    ):
    return db.query(hall_model.Hall).all()


@hall_route.get("/{hall_id}", response_model=hall_registration.HallView)
def get_hall_by_id(
    hall_id: int, db: Session = Depends(get_db)
    ):
    hall = db.query(hall_model.Hall).filter_by(id=hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found.")
    return hall


@hall_route.put("/{hall_id}", response_model=hall_registration.HallView)
def update_hall(
    hall_id: int, payload: hall_registration.HallUpdate, db: Session = Depends(get_db)
):
    hall = db.query(hall_model.Hall).filter_by(id=hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found.")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(hall, field, value)

    db.commit()
    db.refresh(hall)
    return hall


@hall_route.delete("/{hall_id}", status_code=204)
def delete_hall(
    hall_id: int, db: Session = Depends(get_db)
    ):
    hall = db.query(hall_model.Hall).filter_by(id=hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found.")

    db.delete(hall)
    db.commit()
    return

@hall_route.get("/{hall_name}/floors", response_model=list[FloorViewSchema])
def view_floors_hall(
    hall_name: str, db: Session = Depends(get_db)
):
    # Check if the hall name exists
    
    hall = db.query(hall_model.Hall).filter_by(hall_name=hall_name).first()
    if not hall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This hall does not exist."
        )
        
    floors = db.query(HallFloors).filter_by(hall_id=hall.id).all()
    return floors

# edit floor information
@hall_route.put("/{hall_name}/{floor_no}/edit", response_model=FloorViewSchema)
def edit_floor_information(
    hall_name: str, floor_no: int, payload: FloorUpdateSchema, db: Session = Depends(get_db)
):

    # Check if the hall name exists
    hall = db.query(hall_model.Hall).filter_by(hall_name=hall_name).first()
    if not hall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="This hall does not exist."
        )

    # Check if the floor exists withing the specified hall
    floor = db.query(HallFloors).filter_by(hall_id=hall.id, floor_no=floor_no).first()
    if not floor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="This floor does not exist in the specified hall."
        )
        
    # Make the Updates to the floor
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(floor, field, value)
    
    db.commit()
    db.refresh(floor)
    return floor