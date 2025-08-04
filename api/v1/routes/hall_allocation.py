from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.schemas import hall_registration
from api.v1.models import hall as hall_model
from api.db.database import get_db

hall_route = APIRouter(prefix="/hall", tags=["Hall Management"])


@hall_route.post("/", response_model=hall_registration.HallView)
def create_hall(
    payload: hall_registration.HallCreate, db: Session = Depends(get_db)
    ):
    existing = db.query(hall_model.Hall).filter_by(hall_name=payload.hall_name).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="Hall with this name already exists."
        )

    new_hall = hall_model.Hall(**payload.dict())
    db.add(new_hall)
    db.commit()
    db.refresh(new_hall)
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
