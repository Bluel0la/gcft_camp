from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, datetime
from fastapi import Form
from api.v1.schemas.enums import AgeRangeEnum, RegistrationTypeEnum


class UserRegistration(BaseModel):
    """Single-step registration payload — phone number included in body."""

    phone_number: str
    category: str
    first_name: str
    age_range: AgeRangeEnum
    marital_status: str
    no_children: Optional[int] = None
    names_children: Optional[str] = None
    country: str
    state: str
    arrival_date: date
    medical_issues: Optional[str] = None
    local_assembly: Optional[str] = None
    local_assembly_address: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        phone_number: str = Form(...),
        category: str = Form(...),
        first_name: str = Form(...),
        age_range: AgeRangeEnum = Form(...),
        marital_status: str = Form(...),
        country: str = Form(...),
        state: str = Form(...),
        arrival_date: date = Form(...),
        no_children: Optional[int] = Form(None),
        names_children: Optional[str] = Form(None),
        medical_issues: Optional[str] = Form(None),
        local_assembly: Optional[str] = Form(None),
        local_assembly_address: Optional[str] = Form(None),
    ) -> "UserRegistration":
        return cls(
            phone_number=phone_number,
            category=category,
            first_name=first_name,
            age_range=age_range,
            marital_status=marital_status,
            no_children=no_children,
            names_children=names_children,
            country=country,
            state=state,
            arrival_date=arrival_date,
            medical_issues=medical_issues,
            local_assembly=local_assembly,
            local_assembly_address=local_assembly_address,
        )


class UserDisplay(BaseModel):
    """Returned after successful registration."""

    id: int
    first_name: str
    gender: str
    category: str
    registration_type: str
    registration_completed: bool
    hall_name: Optional[str] = None
    floor: Optional[str] = None
    bed_number: Optional[str] = None
    extra_beds: Optional[list[str]] = None
    phone_number: str
    active_status: str
    profile_picture_url: Optional[str] = None
    age_range: str
    marital_status: str
    country: str
    state: str
    arrival_date: date

    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseModel):
    """Lightweight view for listing users."""

    id: int
    first_name: str
    category: str
    registration_type: Optional[str] = None
    registration_completed: Optional[bool] = None
    hall_name: Optional[str] = None
    floor: Optional[str] = None
    bed_number: Optional[str] = None
    extra_beds: Optional[list[str]] = None
    phone_number: str
    profile_picture_url: Optional[str] = None
    active_status: str
    local_assembly: Optional[str] = None
    local_assembly_address: Optional[str] = None
    arrival_date: date
    medical_issues: Optional[str] = None
    state: Optional[str] = None
    gender: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserView(BaseModel):
    """Full detail view of a user."""

    id: int
    first_name: str
    gender: str
    category: str
    registration_type: Optional[str] = None
    registration_completed: Optional[bool] = None
    hall_name: Optional[str] = None
    floor: Optional[str] = None
    bed_number: Optional[str] = None
    extra_beds: Optional[list[str]] = None
    phone_number: Optional[str] = None
    active_status: str
    profile_picture_url: Optional[str] = None
    age_range: str
    marital_status: str
    country: str
    state: str
    arrival_date: date
    no_children: Optional[int] = None
    names_children: Optional[str] = None
    medical_issues: Optional[str] = None
    local_assembly: Optional[str] = None
    local_assembly_address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
