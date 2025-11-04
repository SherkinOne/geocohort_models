from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from models import PyObjectId

class User(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    username: str
    email: str
    hashed_password: str
    role: str  # Can be 'user', 'cmc', 'blockchain'
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str
