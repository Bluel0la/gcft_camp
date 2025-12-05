from api.v1.schemas.Images import ImageCategoryCreate, ImageCategoryView, ImageCreate, ImageView
from fastapi import APIRouter, HTTPException, status, Depends
from api.v1.models.image_categories import ImageCategory
from api.v1.models.images import Image
from sqlalchemy.orm import Session
from api.db.database import get_db


images_route = APIRouter(tags=["Images Management"])

@images_route.get("/categories/", response_model=ImageCategoryView)
def view_image_categories(db: Session = Depends(get_db)):
    categories = db.query(ImageCategory).all()
    return categories

@images_route.post("/categories/", response_model=ImageCategoryView)
def create_image_category(
    payload: ImageCategoryCreate, db: Session = Depends(get_db)
):
    existing_category = (
        db.query(ImageCategory).filter_by(category_name=payload.category_name).first()
    )
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image category already exists.",
        )
    
    new_category = ImageCategory(**payload.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return new_category

@images_route.post("{category_id}/add_image/", response_model=ImageView)
def add_image_to_category(
    category_id: int, payload: ImageCreate, db: Session = Depends(get_db)
):
    category = db.query(ImageCategory).filter_by(id=category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image category not found.",
        )
    
    new_image = Image(**payload.dict(), category_id=category_id)
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    
    return new_image

@images_route.get("/{category_id}/images/", response_model=list[ImageView])
def get_images_by_category(
    category_id: int, db: Session = Depends(get_db)
):
    category = db.query(ImageCategory).filter_by(id=category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image category not found.",
        )
    
    images = db.query(Image).filter_by(category_id=category_id).all()
    return images

@images_route.get("/images/{image_id}/", response_model=ImageView)
def get_image_by_id(
    image_id: int, db: Session = Depends(get_db)
):
    image = db.query(Image).filter_by(id=image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )
    
    return image

@images_route.delete("/images/{image_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    image_id: int, db: Session = Depends(get_db)
):
    image = db.query(Image).filter_by(id=image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )
    
    db.delete(image)
    db.commit()
    
