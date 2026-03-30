"""Programme CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.models.programme import Programme
from api.v1.schemas.programme import ProgrammeCreate, ProgrammeUpdate, ProgrammeView

programme_route = APIRouter(prefix="/programmes", tags=["Programme Management"])


@programme_route.post("/", response_model=ProgrammeView, status_code=201)
def create_programme(payload: ProgrammeCreate, db: Session = Depends(get_db)):
    """Create a new programme/event period."""
    programme = Programme(
        programme_name=payload.programme_name,
        start_date=payload.start_date,
        close_date=payload.close_date,
        registration_status=payload.registration_status.value,
    )
    db.add(programme)
    db.commit()
    db.refresh(programme)
    return programme


@programme_route.get("/", response_model=list[ProgrammeView])
def get_all_programmes(db: Session = Depends(get_db)):
    """List all programmes."""
    return db.query(Programme).order_by(Programme.id.desc()).all()


@programme_route.get("/{programme_id}", response_model=ProgrammeView)
def get_programme(programme_id: int, db: Session = Depends(get_db)):
    """Get a single programme by ID."""
    programme = db.query(Programme).filter(Programme.id == programme_id).first()
    if not programme:
        raise HTTPException(status_code=404, detail="Programme not found.")
    return programme


@programme_route.patch("/{programme_id}", response_model=ProgrammeView)
def update_programme(
    programme_id: int, payload: ProgrammeUpdate, db: Session = Depends(get_db)
):
    """Update programme details (name, dates, registration status)."""
    programme = db.query(Programme).filter(Programme.id == programme_id).first()
    if not programme:
        raise HTTPException(status_code=404, detail="Programme not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Convert enums to their string value
        if hasattr(value, "value"):
            value = value.value
        setattr(programme, field, value)

    db.commit()
    db.refresh(programme)
    return programme


@programme_route.delete("/{programme_id}", status_code=204)
def delete_programme(programme_id: int, db: Session = Depends(get_db)):
    """Delete a programme."""
    programme = db.query(Programme).filter(Programme.id == programme_id).first()
    if not programme:
        raise HTTPException(status_code=404, detail="Programme not found.")
    db.delete(programme)
    db.commit()
    return
