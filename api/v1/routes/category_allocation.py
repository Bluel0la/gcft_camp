from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.schemas import category_registration
from api.v1.models import category as category_model
from api.db.database import get_db


category_route = APIRouter(prefix="/category", tags=["Category Allocation"])


@category_route.post("/", response_model=category_registration.CategoryView)
def create_category(
    payload: category_registration.CategoryCreate, db: Session = Depends(get_db)
):
    existing = (
        db.query(category_model.Category)
        .filter(
            category_model.Category.category_name == payload.category_name,
            category_model.Category.hall_name == payload.hall_name,
            category_model.Category.floor_allocated == payload.floor_allocated,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409, detail="Category allocation already exists."
        )

    new_category = category_model.Category(**payload.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


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

    for field, value in payload.dict(exclude_unset=True).items():
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
