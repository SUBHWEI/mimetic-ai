from app.database.mongodb import get_db
from app.expert_system.matcher import calculate_match
from bson import ObjectId


async def diagnose(symptoms: list[str], min_score: float = 0.2) -> list[dict]:
    db = get_db()
    if db is None:
        return []

    diseases = await db.diseases.find().to_list(length=None)
    results = []

    for disease in diseases:
        matched_count, score = calculate_match(symptoms, disease.get("symptoms", []))
        if score >= min_score:
            results.append({
                "disease_id": str(disease["_id"]),
                "disease_name": disease["name"],
                "description": disease.get("description", ""),
                "severity": disease.get("severity", "moderate"),
                "matched_symptoms": matched_count,
                "total_input_symptoms": len(symptoms),
                "confidence": score,
            })

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results


async def get_treatment(disease_name: str) -> dict | None:
    db = get_db()
    if db is None:
        return None

    # Try exact match first
    treatment = await db.treatments.find_one({"disease_name": disease_name})
    if treatment:
        return {
            "disease_name": treatment["disease_name"],
            "medicines": treatment.get("medicines", []),
            "general_recommendations": treatment.get("general_recommendations", ""),
            "source": treatment.get("source", ""),
        }

    # Fallback: case-insensitive and partial match
    all_tx = await db.treatments.find().to_list(length=None)
    name_lower = disease_name.lower()
    for t in all_tx:
        db_name = t["disease_name"].lower()
        if name_lower in db_name or db_name in name_lower:
            return {
                "disease_name": t["disease_name"],
                "medicines": t.get("medicines", []),
                "general_recommendations": t.get("general_recommendations", ""),
                "source": t.get("source", ""),
            }

    return None
