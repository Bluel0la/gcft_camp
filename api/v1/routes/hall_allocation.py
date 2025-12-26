from api.v1.schemas.floor_management import FloorBedUpdate, FloorViewSchema, FloorUpdateField, FloorUpdateOperation, FloorUpdatePayload
from fastapi import APIRouter, Depends, HTTPException, status
from api.utils.bed_allocation import floor_create_logic
from api.v1.schemas import hall_registration
from api.v1.models import hall as hall_model
from api.v1.models.category import Category
from api.v1.models.floor import HallFloors
from sqlalchemy.orm import Session
from api.db.database import get_db
from sqlalchemy import func
import uuid

hall_route = APIRouter(prefix="/hall", tags=["Hall Management"])

# Create a Hall
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

# Get all Halls
@hall_route.get("/", response_model=list[hall_registration.HallView])
def get_all_halls(
    db: Session = Depends(get_db)
    ):
    return db.query(hall_model.Hall).all()


# Get a hall by it's ID
@hall_route.get("/{hall_id}", response_model=hall_registration.HallView)
def get_hall_by_id(
    hall_id: int, db: Session = Depends(get_db)
    ):
    hall = db.query(hall_model.Hall).filter_by(id=hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found.")
    return hall

# Update a hall's information
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

# Delete a Hall
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

# View the Floors in a Hall
@hall_route.get("/{hall_name}/floors", response_model=list[FloorViewSchema])
def view_floors_hall(
    hall_name: str, db: Session = Depends(get_db)
):
    # Check if the hall name exists
    hall = db.query(hall_model.Hall).filter(
        func.lower(hall_model.Hall.hall_name) == hall_name.lower()
        ).first()
    if not hall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This hall does not exist."
        )

    floors = (
        db.query(HallFloors)
        .filter_by(hall_id=hall.id)
        .order_by(HallFloors.floor_no)
        .all()
    )
    result = []
    for floor in floors:
        result.append(
            FloorViewSchema(
                floor_id=floor.floor_id,
                floor_no=floor.floor_no,
                hall_id=floor.hall_id,
                categories=[cat.id for cat in floor.categories] if floor.categories else [],
                no_beds=floor.no_beds,
                status=floor.status,
                age_ranges=floor.age_ranges
            )
        )
    return result

# Edit the number of beds in a floor
@hall_route.put("/{hall_name}/{floor_no}/editbeds", response_model=FloorViewSchema)
def edit_floor_information(
    hall_name: str, floor_no: int, payload: FloorBedUpdate, db: Session = Depends(get_db)
):

    # Check if the hall name exists
    hall = (
        db.query(hall_model.Hall)
        .filter(func.lower(hall_model.Hall.hall_name) == hall_name.lower())
        .first()
    )
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
        if field == "categories":
            # Expecting a list of category IDs
            if isinstance(value, list):
                categories = db.query(Category).filter(Category.id.in_(value)).all()
                setattr(floor, field, categories)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Categories must be a list of category IDs."
                )
        else:
            setattr(floor, field, value)

    db.commit()
    db.refresh(floor)
    return FloorViewSchema(
        floor_id=floor.floor_id,
        floor_no=floor.floor_no,
        hall_id=floor.hall_id,
        categories=[cat.id for cat in floor.categories] if floor.categories else [],
        no_beds=floor.no_beds,
        status=floor.status,
        age_ranges=floor.age_ranges
    )


# Edit floor attributes like categories and age ranges
@hall_route.patch("/{hall_name}/{floor_no}/update",response_model=FloorViewSchema,)
def update_floor_attributes(
    hall_name: str,
    floor_no: int,
    payload: FloorUpdatePayload,
    db: Session = Depends(get_db),
):
    hall = (
        db.query(hall_model.Hall)
        .filter(func.lower(hall_model.Hall.hall_name) == hall_name.lower())
        .first()
    )
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found.")

    floor = db.query(HallFloors).filter_by(hall_id=hall.id, floor_no=floor_no).first()
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found.")

    # ---- CATEGORY HANDLING ----
    if payload.field == FloorUpdateField.categories:
        if not payload.category_ids:
            raise HTTPException(
                status_code=400,
                detail="category_ids must be provided for category updates.",
            )

        categories = (
            db.query(Category).filter(Category.id.in_(payload.category_ids)).all()
        )

        if payload.operation == FloorUpdateOperation.add:
            for cat in categories:
                if cat not in floor.categories:
                    floor.categories.append(cat)

        elif payload.operation == FloorUpdateOperation.remove:
            for cat in categories:
                if cat in floor.categories:
                    floor.categories.remove(cat)

    # ---- AGE RANGE HANDLING ----
    elif payload.field == FloorUpdateField.age_ranges:
        if not payload.age_ranges:
            raise HTTPException(
                status_code=400,
                detail="age_ranges must be provided for age range updates.",
            )

        current_ranges = set(floor.age_ranges or [])

        if payload.operation == FloorUpdateOperation.add:
            current_ranges.update(payload.age_ranges)

        elif payload.operation == FloorUpdateOperation.remove:
            current_ranges.difference_update(payload.age_ranges)

        floor.age_ranges = list(current_ranges)

    db.commit()
    db.refresh(floor)

    return FloorViewSchema(
        floor_id=floor.floor_id,
        floor_no=floor.floor_no,
        hall_id=floor.hall_id,
        age_ranges=floor.age_ranges,
        categories=[cat.id for cat in floor.categories] if floor.categories else [],
        no_beds=floor.no_beds,
        status=floor.status,
    )