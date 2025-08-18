from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.schemas import category_registration
from api.v1.models import category as category_model, hall as hall_model
from sqlalchemy import func
from api.db.database import get_db


category_route = APIRouter(prefix="/category", tags=["Category Allocation"])


@category_route.post("/", response_model=list[category_registration.CategoryView])
def create_category(
    payload: category_registration.CategoryCreate, db: Session = Depends(get_db)
):
    created = []

    # --- Get hall information ---
    hall = (
        db.query(hall_model.Hall)
        .filter(hall_model.Hall.hall_name == payload.hall_name)
        .first()
    )
    if not hall:
        raise HTTPException(status_code=404, detail="Associated hall not found.")

    # --- Ensure floors are unique ---
    if len(payload.floor_allocated) != len(set(payload.floor_allocated)):
        raise HTTPException(
            status_code=400,
            detail="Duplicate floors detected in the request payload. Each floor must be unique.",
        )

    # --- Validate floors against hall.no_floors ---
    invalid_floors = [
        f for f in payload.floor_allocated if f < 0 or f >= hall.no_floors
    ]
    if invalid_floors:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid floors {invalid_floors} for hall '{hall.hall_name}' "
                f"(valid range: 0 to {hall.no_floors - 1})."
            ),
        )

    # --- Check bed capacity once for all floors ---
    total_category_beds = (
        db.query(func.sum(category_model.Category.no_beds))
        .filter(category_model.Category.hall_name == payload.hall_name)
        .scalar()
        or 0
    )
    requested_beds = payload.no_beds * len(payload.floor_allocated)
    if total_category_beds + requested_beds > hall.no_beds:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Total allocated beds ({total_category_beds + requested_beds}) "
                f"would exceed hall capacity ({hall.no_beds})."
            ),
        )

    # --- Check duplicates in DB first ---
    existing_floors = (
        db.query(category_model.Category.floor_allocated)
        .filter(
            category_model.Category.category_name == payload.category_name,
            category_model.Category.hall_name == payload.hall_name,
            category_model.Category.floor_allocated.in_(payload.floor_allocated),
        )
        .all()
    )
    if existing_floors:
        floor_list = [f[0] for f in existing_floors]
        raise HTTPException(
            status_code=409,
            detail=(
                f"Category '{payload.category_name}' already allocated "
                f"to {payload.hall_name} on floors {floor_list}."
            ),
        )

    # --- Insert all floors ---
    for floor in payload.floor_allocated:
        new_category = category_model.Category(
            category_name=payload.category_name,
            hall_name=payload.hall_name,
            floor_allocated=floor,
            no_beds=payload.no_beds,
        )
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        created.append(new_category)

    return created


@category_route.get("/", response_model=list[category_registration.CategoryView])
def get_all_categories(
    db: Session = Depends(get_db)
    ):
    return db.query(category_model.Category).all()


@category_route.put("/{category_id}", response_model=category_registration.CategoryView)
def update_category(
    category_id: int,
    payload: category_registration.CategoryUpdate,
    db: Session = Depends(get_db),
):
    category = db.query(category_model.Category).filter_by(id=category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")

    updated_data = payload.dict(exclude_unset=True)

    hall_name = updated_data.get("hall_name", category.hall_name)
    new_beds = updated_data.get("no_beds", category.no_beds)

    # Get hall to check total capacity
    hall = db.query(hall_model.Hall).filter_by(hall_name=hall_name).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Associated hall not found.")

    # Calculate current total beds excluding this category
    other_beds = (
        db.query(func.sum(category_model.Category.no_beds))
        .filter(
            category_model.Category.hall_name == hall_name,
            category_model.Category.id != category_id,
        )
        .scalar()
        or 0
    )

    if other_beds + new_beds > hall.no_beds:
        raise HTTPException(
            status_code=400,
            detail=f"Updated allocation ({other_beds + new_beds}) exceeds hall capacity ({hall.no_beds}).",
        )

    # Apply the updates
    for field, value in updated_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


@category_route.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int, db: Session = Depends(get_db)
    ):
    category = db.query(category_model.Category).filter_by(id=category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")

    db.delete(category)
    db.commit()
    return


@category_route.get("/{category_id}", response_model=category_registration.CategoryView)
def get_category_by_id(
    category_id: int, db: Session = Depends(get_db)
    ):
    category = db.query(category_model.Category).filter_by(id=category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    return category
