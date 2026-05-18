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
    first_name: str = ""
    last_name: str = ""
    document_type: str = ""
    document_number: str = ""
    birth_date: str = ""
    country: str = ""
    department: str = ""
    city: str = ""
    phone: str = ""
    verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserInDB(User):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")


class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    first_name: str = ""
    last_name: str = ""
    document_type: str = ""
    document_number: str = ""
    birth_date: str = ""
    country: str = ""
    department: str = ""
    city: str = ""
    phone: str = ""


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
    first_name: str
    last_name: str
    document_type: str
    document_number: str
    birth_date: str
    country: str
    department: str
    city: str
    phone: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
