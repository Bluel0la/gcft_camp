from pydantic import BaseModel
class UserCount(BaseModel):
    total_users: int
    
class UsersMedicalConditions(BaseModel):
    user_name: str
    phone_number: str
    medical_condition: str
