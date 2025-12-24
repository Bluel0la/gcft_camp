from api.v1.schemas.Images import ImageCategoryCreate, ImageCategoryView, ImageCreate, ImageView, List
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from api.utils.file_upload import upload_to_s3, delete_from_s3
from api.v1.models.image_categories import ImageCategory
from api.v1.models.images import Image
from sqlalchemy.orm import Session
from api.db.database import get_db
from dotenv import load_dotenv
load_dotenv(".env")
import os, uuid

images_route = APIRouter(tags=["Images Management"])

@images_route.get("/categories/", response_model=List[ImageCategoryView])
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


@images_route.post("/{category_id}/add_image/", response_model=ImageView)
async def add_image_to_category(
    category_id: int,
    image_name: str = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Check if the category exists
    category = db.query(ImageCategory).filter_by(id=category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image category not found.",
        )
    category_name = category.category_name

    # Check the file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only images are allowed."
        )

    # Auto-rename the image
    ext = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    # Upload the image to AWS
    object_key = f"/{category_name}/{unique_name}"
    file_bytes = await file.read()
    image_url = upload_to_s3(
        file_bytes=file_bytes, object_key=object_key, content_type=file.content_type
    )

    # Save to the DB
    new_image = Image(
        image_name=image_name or unique_name,
        image_url=image_url,
        category_id=category_id,
        status="in-use",
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return new_image


@images_route.get("/{category_id}/images/", response_model=list[ImageView])
def get_images_by_category(
    category_id: int, db: Session = Depends(get_db)
):
    # Check if the Category exists
    category = db.query(ImageCategory).filter_by(id=category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image category not found.",
        )
    
    # Return information on the categories
    images = db.query(Image).filter_by(category_id=category_id).all()
    return images

@images_route.get("/images/{image_id}/", response_model=ImageView)
def get_image_by_id(
    image_id: int, db: Session = Depends(get_db)
):
    # Check if the image exists
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
    # Check if the image exists
    image = db.query(Image).filter_by(id=image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )
        
    # Fetch the images Category
    category_name = db.query(ImageCategory).filter_by(id=image.category_id).first()
    
    # Delete the image from the database
    db.delete(image)
    # Delete the image from Dropbox
    dropbox_path = f"/{category_name}/{image.image_name}"
    delete_from_dropbox(dropbox_path)
    db.commit()
