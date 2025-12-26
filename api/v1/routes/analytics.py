import io
import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.db.database import get_db
from typing import List
from api.v1.models import hall, category, user, phone_number
from api.v1.schemas.analytics import HallAnalytics, CategoryAnalytics, UserCount
from fastapi.responses import StreamingResponse
from api.v1.models.floor import HallFloors

analytics_route = APIRouter(prefix="/analytics", tags=["Analytics"])


@analytics_route.get("/total-users", response_model=UserCount)
def get_total_registered_users(db: Session = Depends(get_db)):
    count = db.query(user.User).count()
    return {"total_users": count}
