from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.schemas.category_registration import CategoryCreate, CategoryView
from api.v1.models.category import Category
from sqlalchemy import func
from api.db.database import get_db


category_route = APIRouter(prefix="/category", tags=["Category Allocation"])


# Create Categories
@category_route.post("/", response_model=CategoryView, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate, db: Session = Depends(get_db)
):

    # Check if the category already exists (case-insensitive)
    existing_category = (
        db.query(Category)
        .filter(func.lower(Category.category_name) == category.category_name.lower())
        .first()
    )
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists."
        )
    new_category = Category(
        category_name=category.category_name
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category

@category_route.get("/", response_model=list[CategoryView])
def get_all_categories(
    db: Session = Depends(get_db)):
    
    categories = db.query(Category).all()
    return categories

@category_route.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int, db: Session = Depends(get_db)
    ):
    category = db.query(Category).filter_by(id=category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")

    db.delete(category)
    db.commit()
    return


@category_route.get("/{category_id}", response_model=CategoryView)
def get_category_by_id(
    category_id: int, db: Session = Depends(get_db)
    ):
    category = db.query(Category).filter_by(id=category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    return category
