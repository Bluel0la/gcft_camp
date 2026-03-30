from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from api.v1.schemas.enums import RegistrationStatusEnum


class ProgrammeCreate(BaseModel):
    programme_name: str
    start_date: date
    close_date: date
    registration_status: RegistrationStatusEnum = RegistrationStatusEnum.open


class ProgrammeUpdate(BaseModel):
    programme_name: Optional[str] = None
    start_date: Optional[date] = None
    close_date: Optional[date] = None
    registration_status: Optional[RegistrationStatusEnum] = None


class ProgrammeView(BaseModel):
    id: int
    programme_name: str
    start_date: date
    close_date: date
    registration_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
