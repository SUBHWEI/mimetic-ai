from app.database.mongodb import get_db
from app.expert_system.matcher import calculate_match, build_symptom_weights
import re
import unicodedata


def _strip_accents(s: str) -> str:
    """Remove accents (NFD normalization + filtering combining marks)."""
    nfkd = unicodedata.normalize('NFKD', s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


async def diagnose(
    symptoms: list[str],
    min_score: float = 0.2,
    patient_info: dict | None = None,
) -> list[dict]:
    db = get_db()
    if db is None:
        return []

    diseases = await db.diseases.find().to_list(length=None)
    weights = build_symptom_weights(diseases)

    # Compute demographic adjustment once per patient, not per disease.
    demo = _demographic_profile(patient_info or {})

    results = []
    for disease in diseases:
        matched_count, score = calculate_match(
            symptoms, disease.get("symptoms", []), weights
        )
        if patient_info:
            score = _apply_demographic_adjustment(
                disease, score, demo
            )
        if score >= min_score:
            results.append({
                "disease_id": str(disease["_id"]),
                "disease_name": disease["name"],
                "description": disease.get("description", ""),
                "severity": disease.get("severity", "moderate"),
                "matched_symptoms": matched_count,
                "total_input_symptoms": len(symptoms),
                "disease_symptoms": disease.get("symptoms", []),
                "confidence": score,
            })

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results


def _demographic_profile(patient_info: dict) -> dict:
    """Extract age/sex/bmi once from patient_info with robust parsing."""
    age = None
    raw_age = patient_info.get("age")
    if raw_age is not None:
        try:
            age = float(raw_age)
        except (ValueError, TypeError):
            try:
                birth = str(raw_age)
                # "YYYY-MM-DD" birthdate -> approximate age
                if re.match(r"\d{4}-\d{2}-\d{2}", birth):
                    import datetime
                    b = datetime.date.fromisoformat(birth[:10])
                    age = (datetime.date.today() - b).days / 365.25
            except (ValueError, TypeError):
                pass

    sex = ""
    raw_sex = str(patient_info.get("gender", patient_info.get("sex", ""))).lower()
    if "masc" in raw_sex or raw_sex == "m" or "hombr" in raw_sex:
        sex = "male"
    elif "fem" in raw_sex or raw_sex == "f" or "mujer" in raw_sex:
        sex = "female"

    return {"age": age, "sex": sex}


def _apply_demographic_adjustment(disease: dict, score: float, profile: dict) -> float:
    """Apply a soft multiplier to the score based on patient age/sex.

    Returns the adjusted score (clamped to [0, 1]). Uses keyword heuristics
    on the disease name to avoid needing a curated age range database.
    """
    if score <= 0:
        return score

    name = _strip_accents(disease["name"].lower())
    age = profile.get("age")
    sex = profile.get("sex")

    factor = 1.0

    # --- Age-based adjustments ---
    if age is not None:
        if "infarto" in name or "miocardio" in name or ("trombosis" in name and "venosa profunda" not in name):
            # Ischemic events much more likely with age
            if age >= 45:
                factor *= 1.25
            else:
                factor *= 0.55

        if "apendicitis" in name:
            if 30 <= age <= 50:
                factor *= 0.9
            elif age < 20:
                factor *= 1.1

        if "prostat" in name:
            if age < 50:
                factor *= 0.4
            else:
                factor *= 1.3

        if "menopaus" in name:
            if age < 40:
                factor *= 0.3

        if "pediatr" in name or "sarampion" in name or "varicela" in name:
            if age >= 18:
                factor *= 0.5
            else:
                factor *= 1.2

        if "osteoporosis" in name:
            if age < 50:
                factor *= 0.5

        if "parkinson" in name:
            if age < 55:
                factor *= 0.6

    # --- Sex-based adjustments ---
    if sex == "male" and "prostat" in name:
        factor *= 1.2
    if sex == "female" and "prostat" in name:
        factor *= 0.2
    if sex == "female" and "menopaus" in name:
        factor *= 2.0
    if sex == "female" and "endometriosis" in name:
        factor *= 1.5
    if sex == "female" and "embarazo" in name:
        factor *= 1.5
    if sex == "male" and ("endometriosis" in name or "embarazo" in name or "menopaus" in name):
        factor *= 0.2

    return round(min(max(score * factor, 0.0), 1.0), 2)


async def get_treatment(disease_name: str) -> dict | None:
    db = get_db()
    if db is None:
        return None

    # Try exact match first
    treatment = await db.treatments.find_one({"disease_name": disease_name})
    if treatment:
        return _build_treatment_response(treatment)

    # Fallback: case-insensitive and partial match (with accent normalization)
    all_tx = await db.treatments.find().to_list(length=None)
    name_lower = _strip_accents(disease_name.lower())
    for t in all_tx:
        db_name = _strip_accents(t["disease_name"].lower())
        if name_lower in db_name or db_name in name_lower:
            return _build_treatment_response(t)

    return None


def _build_treatment_response(treatment: dict) -> dict:
    return {
        "disease_name": treatment["disease_name"],
        "medicines": treatment.get("medicines", []),
        "alternative_medicines": treatment.get("alternative_medicines", []),
        "non_pharmacological_treatments": treatment.get("non_pharmacological_treatments", []),
        "general_recommendations": treatment.get("general_recommendations", ""),
        "source": treatment.get("source", ""),
    }


async def recommend_treatment(disease_name: str, patient_info: dict) -> dict | None:
    treatment = await get_treatment(disease_name)
    if not treatment:
        return None

    try:
        return _recommend_treatment_impl(treatment, patient_info)
    except Exception:
        return None


def _recommend_treatment_impl(treatment: dict, patient_info: dict) -> dict | None:
    raw_allergies = patient_info.get("allergies", "")
    allergies = [a.strip() for a in raw_allergies.split(",") if a.strip()] if isinstance(raw_allergies, str) else (raw_allergies if isinstance(raw_allergies, list) else [])
    raw_comorbidities = patient_info.get("comorbidities", "") or patient_info.get("medical_history", "")
    comorbidities = [c.strip() for c in raw_comorbidities.split(",") if c.strip()] if isinstance(raw_comorbidities, str) else (raw_comorbidities if isinstance(raw_comorbidities, list) else [])
    raw_preg = patient_info.get("pregnancy", False)
    if isinstance(raw_preg, str):
        pregnancy = raw_preg.lower() in ("true", "si", "sí", "yes", "1")
    else:
        pregnancy = bool(raw_preg)
    weight_str = patient_info.get("weight", "")
    try:
        weight = float(weight_str) if weight_str else None
    except (ValueError, TypeError):
        weight = None

    available = []
    not_recommended = []

    for medicine in treatment.get("medicines", []):
        contraindications = medicine.get("contraindications", {})
        adjustments = medicine.get("adjustments", {})

        reasons = []
        dosages = medicine.get("dosage", "")

        med_allergies = contraindications.get("allergies", [])
        for allergy in allergies:
            if any(allergy.lower() in ma.lower() for ma in med_allergies):
                reasons.append(f"Alergia a {allergy}")
                break

        med_conditions = contraindications.get("conditions", [])
        for condition in comorbidities:
            if any(
                condition.lower() in mc.lower() or mc.lower() in condition.lower()
                for mc in med_conditions
            ):
                reasons.append(f"Contraindicado en {condition}")
                break

        if pregnancy:
            pregnancy_adj = adjustments.get("pregnancy")
            if pregnancy_adj:
                txt = pregnancy_adj.lower()
                if "contraindicado" in txt or "evitar" in txt or "categoría c" in txt or "categoría d" in txt or "categoría x" in txt:
                    reasons.append(f"Contraindicado en embarazo: {pregnancy_adj}")

        calculated_dosage = None
        dosage_mg_kg = medicine.get("dosage_mg_kg")
        if dosage_mg_kg and weight:
            m = re.search(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*mg/kg", str(dosage_mg_kg))
            if m:
                lo, hi = float(m.group(1)), float(m.group(2))
                calculated_dosage = f"{lo * weight:.0f}-{hi * weight:.0f} mg/dosis"
            else:
                m = re.search(r"(\d+(?:\.\d+)?)\s*mg/kg", str(dosage_mg_kg))
                if m:
                    d = float(m.group(1))
                    calculated_dosage = f"{d * weight:.0f} mg/dosis"

        entry = {
            "name": medicine.get("name"),
            "dosage": dosages,
            "dosage_mg_kg": dosage_mg_kg,
            "max_daily_dose": medicine.get("max_daily_dose"),
            "frequency": medicine.get("frequency"),
            "duration": medicine.get("duration"),
            "route": medicine.get("route"),
            "calculated_dosage": calculated_dosage,
            "contraindications": contraindications,
            "adjustments": adjustments,
            "interactions_warning": medicine.get("interactions_warning"),
            "monitoring": medicine.get("monitoring"),
            "patient_summary": medicine.get("patient_summary"),
        }

        if reasons:
            entry["reasons"] = reasons
            not_recommended.append(entry)
        else:
            available.append(entry)

    alternatives = []
    for alt in treatment.get("alternative_medicines", []):
        alternatives.append({
            "name": alt.get("name"),
            "dosage_mg_kg": alt.get("dosage_mg_kg"),
            "max_daily_dose": alt.get("max_daily_dose"),
            "frequency": alt.get("frequency"),
            "duration": alt.get("duration"),
            "route": alt.get("route"),
            "contraindications": alt.get("contraindications"),
            "adjustments": alt.get("adjustments"),
            "interactions_warning": alt.get("interactions_warning"),
            "monitoring": alt.get("monitoring"),
            "patient_summary": alt.get("patient_summary"),
        })

    return {
        "disease_name": treatment["disease_name"],
        "available": available,
        "not_recommended": not_recommended,
        "alternatives": alternatives,
        "non_pharmacological": treatment.get("non_pharmacological_treatments", []),
        "general_recommendations": treatment.get("general_recommendations", ""),
    }


def extract_symptoms_from_vitals(patient_info: dict) -> list[str]:
    symptoms = []

    temp = patient_info.get("temperature")
    if temp is not None:
        try:
            t = float(temp)
            if t > 39:
                symptoms.append("fiebre alta persistente")
            elif t > 37.5:
                symptoms.append("fiebre")
        except (ValueError, TypeError):
            pass

    bp = patient_info.get("blood_pressure")
    if bp:
        try:
            parts = str(bp).split("/")
            if len(parts) == 2:
                systolic = float(parts[0])
                diastolic = float(parts[1])
                if systolic > 140 or diastolic > 90:
                    symptoms.append("presión arterial alta")
                elif systolic < 90 or diastolic < 60:
                    symptoms.append("presión arterial baja")
        except (ValueError, TypeError):
            pass

    hr = patient_info.get("heart_rate")
    if hr is not None:
        try:
            h = float(hr)
            if h > 100:
                symptoms.append("taquicardia")
            elif h < 60:
                symptoms.append("bradicardia")
        except (ValueError, TypeError):
            pass

    rr = patient_info.get("respiratory_rate")
    if rr is not None:
        try:
            r = float(rr)
            if r > 20:
                symptoms.append("taquipnea")
        except (ValueError, TypeError):
            pass

    weight = patient_info.get("weight")
    height = patient_info.get("height")
    if weight is not None and height is not None:
        try:
            w = float(weight)
            h = float(height)
            if h > 0:
                bmi = w / (h / 100) ** 2
                if bmi > 30:
                    symptoms.append("obesidad")
                elif bmi > 25:
                    symptoms.append("sobrepeso")
                elif bmi < 18.5:
                    symptoms.append("desnutrición")
        except (ValueError, TypeError):
            pass

    return symptoms


def narrow_diagnoses(
    diagnoses: list[dict],
    symptoms: list[str],
    min_confidence: float = 0.25,
    max_gap: float = 0.25,
) -> list[dict]:
    """Filter diagnoses to the most relevant ones.

    - Drops any diagnosis below ``min_confidence`` absolute score.
    - Drops diagnoses that fall more than ``max_gap`` below the top one
      (even if above the absolute threshold), to avoid showing a "3rd"
      candidate that is almost irrelevant compared to the leader.
    """
    if not diagnoses or not symptoms:
        return diagnoses

    for d in diagnoses:
        disease_symptoms = d.get("disease_symptoms", [])
        if disease_symptoms:
            present = sum(1 for s in symptoms if s in disease_symptoms)
            d["secondary_score"] = present / len(disease_symptoms)
        else:
            d["secondary_score"] = 0

    sorted_diags = sorted(
        diagnoses,
        key=lambda x: (x.get("confidence", 0), x.get("secondary_score", 0)),
        reverse=True,
    )

    if not sorted_diags:
        return sorted_diags

    top_conf = sorted_diags[0].get("confidence", 0)

    kept = []
    for d in sorted_diags:
        conf = d.get("confidence", 0)
        if conf < min_confidence:
            continue
        if top_conf - conf > max_gap:
            continue
        kept.append(d)
        if len(kept) >= 3:
            break

    return kept or sorted_diags[:1]


def merge_vital_symptoms(patient_info: dict, existing_symptoms: list[str]) -> list[str]:
    vital = extract_symptoms_from_vitals(patient_info)
    seen = set(existing_symptoms)
    combined = list(existing_symptoms)
    for s in vital:
        if s not in seen:
            combined.append(s)
            seen.add(s)
    return combined
