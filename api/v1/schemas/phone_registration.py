from pydantic import BaseModel
from datetime import datetime


class PhoneNumberBase(BaseModel):
    phone_number: str


class PhoneNumberRegistration(PhoneNumberBase):
    pass


class PhoneNumberView(PhoneNumberBase):
    id: int
    time_registered: datetime

    class Config:
        orm_mode = True
