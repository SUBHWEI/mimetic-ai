from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database.mongodb import get_db
from bson import ObjectId

router = APIRouter()


class SymptomCreate(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None


class DiseaseCreate(BaseModel):
    name: str
    description: str | None = None
    symptoms: list[str]
    severity: str = "moderate"


class MedicineItem(BaseModel):
    name: str
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None


class TreatmentCreate(BaseModel):
    disease_name: str
    medicines: list[MedicineItem]
    general_recommendations: str | None = None
    source: str | None = None


@router.post("/symptoms")
async def create_symptom(data: SymptomCreate):
    db = get_db()
    result = await db.symptoms.insert_one(data.model_dump())
    return {"id": str(result.inserted_id), "name": data.name}


@router.get("/symptoms")
async def list_symptoms():
    db = get_db()
    symptoms = await db.symptoms.find().to_list(length=None)
    return [
        {"id": str(s["_id"]), "name": s["name"], "description": s.get("description"), "category": s.get("category")}
        for s in symptoms
    ]


@router.post("/diseases")
async def create_disease(data: DiseaseCreate):
    db = get_db()
    result = await db.diseases.insert_one(data.model_dump())
    return {"id": str(result.inserted_id), "name": data.name}


@router.get("/diseases")
async def list_diseases():
    db = get_db()
    diseases = await db.diseases.find().to_list(length=None)
    return [
        {
            "id": str(d["_id"]),
            "name": d["name"],
            "description": d.get("description"),
            "symptoms": d.get("symptoms", []),
            "severity": d.get("severity"),
        }
        for d in diseases
    ]


@router.post("/treatments")
async def create_treatment(data: TreatmentCreate):
    db = get_db()
    result = await db.treatments.insert_one(data.model_dump())
    return {"id": str(result.inserted_id), "disease_name": data.disease_name}


@router.get("/treatments")
async def list_treatments():
    db = get_db()
    treatments = await db.treatments.find().to_list(length=None)
    return [
        {
            "id": str(t["_id"]),
            "disease_name": t["disease_name"],
            "medicines": t.get("medicines", []),
            "general_recommendations": t.get("general_recommendations"),
        }
        for t in treatments
    ]
