from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.database.mongodb import get_db
from app.auth.permissions import require_roles
from app.utils import normalize_text
from bson import ObjectId
from typing import Optional, Any

router = APIRouter()


class SymptomCreate(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None


class SymptomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class DiseaseCreate(BaseModel):
    name: str
    description: str | None = None
    symptoms: list[str] = []
    severity: str = "moderate"


class DiseaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    symptoms: Optional[list[str]] = None
    severity: Optional[str] = None


class MedicineItem(BaseModel):
    name: str
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None


class TreatmentUpdate(BaseModel):
    disease_name: Optional[str] = None
    medicines: Optional[list[Any]] = None
    general_recommendations: Optional[str] = None
    source: Optional[str] = None


class MedicineCreate(BaseModel):
    name: str
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None


class TreatmentCreate(BaseModel):
    disease_name: str
    medicines: list[Any] = []
    general_recommendations: str | None = None
    source: str | None = None


def _symptom_out(s: dict) -> dict:
    return {"id": str(s["_id"]), "name": s["name"], "description": s.get("description"), "category": s.get("category")}


def _disease_out(d: dict) -> dict:
    return {
        "id": str(d["_id"]),
        "name": d["name"],
        "description": d.get("description"),
        "symptoms": d.get("symptoms", []),
        "severity": d.get("severity"),
    }


def _treatment_out(t: dict) -> dict:
    return {
        "id": str(t["_id"]),
        "disease_name": t["disease_name"],
        "medicines": t.get("medicines", []),
        "general_recommendations": t.get("general_recommendations"),
        "source": t.get("source"),
    }


def _non_empty(data: dict) -> dict:
    return {k: v for k, v in data.items() if v is not None and v != ""}


# ── Symptoms ─────────────────────────────────────────────────────

@router.post("/symptoms")
async def create_symptom(
    data: SymptomCreate,
    current_user=Depends(require_roles("admin", "super_admin")),
):
    db = get_db()
    name = normalize_text(data.name)
    if not name:
        raise HTTPException(status_code=422, detail="Nombre inválido")
    existing = await db.symptoms.find_one({"name": name})
    if existing:
        raise HTTPException(status_code=409, detail="El síntoma ya existe")
    result = await db.symptoms.insert_one({"name": name, "description": data.description, "category": data.category})
    return {"id": str(result.inserted_id), "name": name}


@router.get("/symptoms")
async def list_symptoms(current_user=Depends(require_roles("medico", "admin", "super_admin"))):
    db = get_db()
    symptoms = await db.symptoms.find().to_list(length=None)
    return [_symptom_out(s) for s in symptoms]


@router.put("/symptoms/{symptom_id}")
async def update_symptom(
    symptom_id: str,
    data: SymptomUpdate,
    current_user=Depends(require_roles("admin", "super_admin")),
):
    db = get_db()
    update = _non_empty(data.model_dump())
    if not update:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    if "name" in update:
        update["name"] = normalize_text(update["name"])
        dup = await db.symptoms.find_one({"name": update["name"], "_id": {"$ne": ObjectId(symptom_id)}})
        if dup:
            raise HTTPException(status_code=409, detail="Otro síntoma ya usa ese nombre")
    res = await db.symptoms.update_one({"_id": ObjectId(symptom_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Síntoma no encontrado")
    doc = await db.symptoms.find_one({"_id": ObjectId(symptom_id)})
    return _symptom_out(doc)


@router.delete("/symptoms/{symptom_id}")
async def delete_symptom(
    symptom_id: str,
    current_user=Depends(require_roles("admin", "super_admin")),
):
    db = get_db()
    res = await db.symptoms.delete_one({"_id": ObjectId(symptom_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Síntoma no encontrado")
    return {"deleted": True, "id": symptom_id}


# ── Diseases ─────────────────────────────────────────────────────

@router.post("/diseases")
async def create_disease(
    data: DiseaseCreate,
    current_user=Depends(require_roles("admin", "super_admin")),
):
    db = get_db()
    name = normalize_text(data.name)
    if not name:
        raise HTTPException(status_code=422, detail="Nombre inválido")
    existing = await db.diseases.find_one({"name": name})
    if existing:
        raise HTTPException(status_code=409, detail="La enfermedad ya existe")
    result = await db.diseases.insert_one({"name": name, "description": data.description, "symptoms": [normalize_text(s) for s in data.symptoms if normalize_text(s)], "severity": data.severity})
    return {"id": str(result.inserted_id), "name": name}


@router.get("/diseases")
async def list_diseases(current_user=Depends(require_roles("medico", "admin", "super_admin"))):
    db = get_db()
    diseases = await db.diseases.find().to_list(length=None)
    return [_disease_out(d) for d in diseases]


@router.put("/diseases/{disease_id}")
async def update_disease(
    disease_id: str,
    data: DiseaseUpdate,
    current_user=Depends(require_roles("admin", "super_admin")),
):
    db = get_db()
    update = _non_empty(data.model_dump())
    if not update:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    if update.get("name"):
        update["name"] = normalize_text(update["name"])
        dup = await db.diseases.find_one({"name": update["name"], "_id": {"$ne": ObjectId(disease_id)}})
        if dup:
            raise HTTPException(status_code=409, detail="Otra enfermedad ya usa ese nombre")
    if update.get("symptoms"):
        update["symptoms"] = list({normalize_text(s) for s in update["symptoms"] if normalize_text(s)})
    res = await db.diseases.update_one({"_id": ObjectId(disease_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Enfermedad no encontrada")
    doc = await db.diseases.find_one({"_id": ObjectId(disease_id)})
    return _disease_out(doc)


@router.delete("/diseases/{disease_id}")
async def delete_disease(
    disease_id: str,
    current_user=Depends(require_roles("admin", "super_admin")),
):
    db = get_db()
    res = await db.diseases.delete_one({"_id": ObjectId(disease_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Enfermedad no encontrada")
    return {"deleted": True, "id": disease_id}


# ── Treatments ───────────────────────────────────────────────────

@router.post("/treatments")
async def create_treatment(
    data: TreatmentCreate,
    current_user=Depends(require_roles("admin", "super_admin")),
):
    db = get_db()
    disease_name = normalize_text(data.disease_name)
    if not disease_name:
        raise HTTPException(status_code=422, detail="Disease name inválido")
    existing = await db.treatments.find_one({"disease_name": disease_name})
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un tratamiento para esta enfermedad")
    result = await db.treatments.insert_one({"disease_name": disease_name, "medicines": data.medicines, "general_recommendations": data.general_recommendations, "source": data.source})
    return {"id": str(result.inserted_id), "disease_name": disease_name}


@router.get("/treatments")
async def list_treatments(current_user=Depends(require_roles("medico", "admin", "super_admin"))):
    db = get_db()
    treatments = await db.treatments.find().to_list(length=None)
    return [_treatment_out(t) for t in treatments]


@router.put("/treatments/{treatment_id}")
async def update_treatment(
    treatment_id: str,
    data: TreatmentUpdate,
    current_user=Depends(require_roles("admin", "super_admin")),
):
    db = get_db()
    update = _non_empty(data.model_dump())
    if not update:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    if update.get("disease_name"):
        update["disease_name"] = normalize_text(update["disease_name"])
        dup = await db.treatments.find_one({"disease_name": update["disease_name"], "_id": {"$ne": ObjectId(treatment_id)}})
        if dup:
            raise HTTPException(status_code=409, detail="Ya existe otro tratamiento para esa enfermedad")
    res = await db.treatments.update_one({"_id": ObjectId(treatment_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    doc = await db.treatments.find_one({"_id": ObjectId(treatment_id)})
    return _treatment_out(doc)


@router.delete("/treatments/{treatment_id}")
async def delete_treatment(
    treatment_id: str,
    current_user=Depends(require_roles("admin", "super_admin")),
):
    db = get_db()
    res = await db.treatments.delete_one({"_id": ObjectId(treatment_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return {"deleted": True, "id": treatment_id}


# ── Bulk import (ingreso masivo) ─────────────────────────────────

class BulkImport(BaseModel):
    collection: str  # symptoms | diseases | treatments
    documents: list[dict]
    key_field: str = "name"


@router.post("/bulk")
async def bulk_import(
    data: BulkImport,
    current_user=Depends(require_roles("admin", "super_admin")),
):
    db = get_db()
    if data.collection not in ("symptoms", "diseases", "treatments"):
        raise HTTPException(status_code=400, detail="La colección debe ser symptoms, diseases o treatments")
    coll = db[data.collection]
    from pymongo.errors import DuplicateKeyError
    inserted = 0
    updated = 0
    errores = []
    for i, doc in enumerate(data.documents):
        key = normalize_text(doc.get(data.key_field) or "")
        if not key:
            errores.append({"index": i, "reason": "missing key field"})
            continue
        patch = {k: v for k, v in doc.items() if k != "_id"}
        patch[data.key_field] = key
        try:
            res = await coll.update_one({data.key_field: key}, {"$set": patch}, upsert=True)
        except DuplicateKeyError:
            errores.append({"index": i, "reason": "duplicate key (posible colisión con acentos previos)"})
            continue
        if res.upserted_id is not None:
            inserted += 1
        else:
            updated += 1
    return {"inserted": inserted, "updated": updated, "errors": errores}


# ── Integridad ───────────────────────────────────────────────────

@router.get("/integrity")
async def integrity_check(current_user=Depends(require_roles("medico", "admin", "super_admin"))):
    db = get_db()
    report = {"missing_symptoms": [], "treatments_without_disease": [], "diseases_without_treatment": []}

    all_symptoms = await db.symptoms.find({}, {"name": 1}).to_list(length=None)
    sym_names = {s["name"].lower().strip() for s in all_symptoms}

    diseases = await db.diseases.find({}).to_list(length=None)
    disease_names = {d["name"].lower().strip() for d in diseases}

    for d in diseases:
        for sym in d.get("symptoms", []):
            if sym.lower().strip() not in sym_names:
                report["missing_symptoms"].append({"disease": d["name"], "symptom": sym})

    treatments = await db.treatments.find({}, {"disease_name": 1}).to_list(length=None)
    treatment_names = {t["disease_name"].lower().strip() for t in treatments}

    for t in treatments:
        if t["disease_name"].lower().strip() not in disease_names:
            report["treatments_without_disease"].append(t["disease_name"])

    for dn in disease_names:
        if dn not in treatment_names:
            report["diseases_without_treatment"].append(dn)

    return report
