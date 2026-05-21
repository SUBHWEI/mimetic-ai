from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from datetime import datetime


class ClinicalHistory(BaseModel):
    id: Optional[str] = None
    document_number: str
    document_type: str = "CC"
    first_name: str = ""
    last_name: str = ""
    birth_date: str = ""
    age: str = ""
    gender: str = ""
    occupation: str = ""
    phone: str = ""
    country: str = ""
    department: str = ""
    city: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ClinicalHistoryInDB(ClinicalHistory):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")


class ClinicalHistoryCreate(BaseModel):
    document_number: str
    document_type: str = "CC"
    first_name: str = ""
    last_name: str = ""
    birth_date: str = ""
    age: str = ""
    gender: str = ""
    occupation: str = ""
    phone: str = ""
    country: str = ""
    department: str = ""
    city: str = ""


class ClinicalHistoryOut(BaseModel):
    id: str
    document_number: str
    document_type: str
    first_name: str
    last_name: str
    birth_date: str
    age: str
    gender: str
    occupation: str
    phone: str
    country: str
    department: str
    city: str
    created_at: datetime
    updated_at: datetime


# ── Session ──────────────────────────────────────────────────────

class Session(BaseModel):
    id: Optional[str] = None
    document_number: str
    doctor_id: str
    doctor_name: str = ""
    date: datetime = Field(default_factory=datetime.utcnow)
    consultation_reason: str = ""
    symptom_evolution: str = ""
    tobacco: str = ""
    alcohol: str = ""
    substances: str = ""
    physical_activity: str = ""
    medical_history: str = ""
    surgical_history: str = ""
    pharmacological_history: str = ""
    allergies: str = ""
    blood_pressure: str = ""
    heart_rate: str = ""
    respiratory_rate: str = ""
    temperature: str = ""
    weight: str = ""
    height: str = ""
    symptoms: list[str] = []
    diagnoses: list[dict] = []
    treatment: Optional[dict] = None
    report_html: str = ""


class SessionInDB(Session):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")


class SessionCreate(BaseModel):
    consultation_reason: str = ""
    symptom_evolution: str = ""
    tobacco: str = ""
    alcohol: str = ""
    substances: str = ""
    physical_activity: str = ""
    medical_history: str = ""
    surgical_history: str = ""
    pharmacological_history: str = ""
    allergies: str = ""
    blood_pressure: str = ""
    heart_rate: str = ""
    respiratory_rate: str = ""
    temperature: str = ""
    weight: str = ""
    height: str = ""


class SessionUpdate(BaseModel):
    symptoms: list[str] = []
    diagnoses: list[dict] = []
    treatment: Optional[dict] = None
    report_html: str = ""


class SessionOut(BaseModel):
    id: str
    document_number: str
    doctor_id: str
    doctor_name: str
    date: datetime
    consultation_reason: str
    symptom_evolution: str
    tobacco: str
    alcohol: str
    substances: str
    physical_activity: str
    medical_history: str
    surgical_history: str
    pharmacological_history: str
    allergies: str
    blood_pressure: str
    heart_rate: str
    respiratory_rate: str
    temperature: str
    weight: str
    height: str
    symptoms: list[str]
    diagnoses: list[dict]
    treatment: Optional[dict]
    report_html: str


# ── Search ───────────────────────────────────────────────────────

class SearchResultItem(BaseModel):
    document_number: str
    first_name: str = ""
    last_name: str = ""
    document_type: str = ""
    source: str = ""  # "clinical_history", "user", "both"
    has_clinical_history: bool = False
    has_user_account: bool = False
    base_data: dict = {}
