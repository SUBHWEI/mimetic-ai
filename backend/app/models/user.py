from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from datetime import datetime


class User(BaseModel):
    id: Optional[str] = None
    email: str
    name: str
    password_hash: str
    role: str = "paciente"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserInDB(User):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")


class UserCreate(BaseModel):
    email: str
    name: str
    password: str


class UserCreateByAdmin(BaseModel):
    email: str
    name: str
    password: str
    role: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
