from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.schemas import hall_registration
from api.v1.models import hall as hall_model
from api.db.database import get_db
from api.utils.bed_allocation import floor_create_logic
from api.v1.schemas.floor_management import FloorUpdateSchema, FloorViewSchema
from sqlalchemy import func
from api.v1.models.category import Category
import uuid
from api.v1.models.floor import HallFloors

hall_route = APIRouter(prefix="/hall", tags=["Hall Management"])


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
            )
        )
    return result

# edit floor information
@hall_route.put("/{hall_name}/{floor_no}/edit", response_model=FloorViewSchema)
def edit_floor_information(
    hall_name: str, floor_no: int, payload: FloorUpdateSchema, db: Session = Depends(get_db)
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
    )


@hall_route.post(
    "/{hall_name}/{floor_no}/categories/add", response_model=FloorViewSchema
)
def add_categories_to_floor(
    hall_name: str,
    floor_no: int,
    category_ids: list[int],
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

    categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
    for cat in categories:
        if cat not in floor.categories:
            floor.categories.append(cat)
    db.commit()
    db.refresh(floor)
    return FloorViewSchema(
        floor_id=floor.floor_id,
        floor_no=floor.floor_no,
        hall_id=floor.hall_id,
        categories=[cat.id for cat in floor.categories] if floor.categories else [],
        no_beds=floor.no_beds,
        status=floor.status,
    )


@hall_route.post(
    "/{hall_name}/{floor_no}/categories/remove", response_model=FloorViewSchema
)
def remove_categories_from_floor(
    hall_name: str,
    floor_no: int,
    category_ids: list[int],
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

    categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
    for cat in categories:
        if cat in floor.categories:
            floor.categories.remove(cat)
    db.commit()
    db.refresh(floor)
    return FloorViewSchema(
        floor_id=floor.floor_id,
        floor_no=floor.floor_no,
        hall_id=floor.hall_id,
        categories=[cat.id for cat in floor.categories] if floor.categories else [],
        no_beds=floor.no_beds,
        status=floor.status,
    )


@hall_route.post(
    "/{hall_name}/{floor_no}/age_ranges/add", response_model=FloorViewSchema
)
def add_age_ranges_to_floor(
    hall_name: str,
    floor_no: int,
    age_ranges: list[str],
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

    # Add new age ranges, avoiding duplicates
    current_ranges = set(floor.age_ranges or [])
    for ar in age_ranges:
        current_ranges.add(ar)
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


@hall_route.post(
    "/{hall_name}/{floor_no}/age_ranges/remove", response_model=FloorViewSchema
)
def remove_age_ranges_from_floor(
    hall_name: str,
    floor_no: int,
    age_ranges: list[str],
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

    # Remove specified age ranges
    current_ranges = set(floor.age_ranges or [])
    for ar in age_ranges:
        current_ranges.discard(ar)
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
