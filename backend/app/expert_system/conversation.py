"""Conversational engine for interactive diagnosis."""

from app.expert_system.engine import diagnose
from app.database.mongodb import get_db

MAX_CANDIDATES_FOR_SUGGESTIONS = 5
TARGET_DIAGNOSES_COUNT = 3
MAX_FOLLOWUP_SUGGESTIONS = 4


async def generate_followup(symptoms: list[str]) -> dict:
    """Generate follow-up question based on current symptoms.

    Returns:
        dict with:
            - question: str (the follow-up question)
            - suggestions: list[str] (symptoms to suggest asking about)
            - diagnoses: list[dict] (current top diagnoses)
            - ready: bool (if we have few enough diagnoses)
    """
    results = await diagnose(symptoms)
    if not results:
        return {
            "question": "No encontré enfermedades que coincidan con esos síntomas. ¿Podrías describir mejor los síntomas?",
            "suggestions": [],
            "diagnoses": [],
            "ready": False,
        }

    # If we have few enough, we're ready
    if len(results) <= TARGET_DIAGNOSES_COUNT:
        return {
            "question": "",
            "suggestions": [],
            "diagnoses": results,
            "ready": True,
        }

    top = results[:MAX_CANDIDATES_FOR_SUGGESTIONS]
    top_names = {d["disease_name"] for d in top}

    db = get_db()
    if db is None:
        return {"question": "", "suggestions": [], "diagnoses": results, "ready": True}

    # Get full disease docs for top candidates
    disease_docs = await db.diseases.find(
        {"name": {"$in": list(top_names)}}
    ).to_list(length=None)

    # Collect all symptoms from top diseases, excluding already-mentioned ones
    symptom_set = set(s.lower().strip() for s in symptoms)
    candidate_symptoms: dict[str, int] = {}

    for doc in disease_docs:
        for sym in doc.get("symptoms", []):
            s = sym.lower().strip()
            if s not in symptom_set:
                candidate_symptoms[s] = candidate_symptoms.get(s, 0) + 1

    # Sort symptoms by how many top diseases they appear in (most discriminative first)
    scored = sorted(candidate_symptoms.items(), key=lambda x: -x[1])

    # Pick symptoms that differentiate well
    picks = []
    seen_scores = set()
    for sym, count in scored:
        if count not in seen_scores or len(picks) < 2:
            picks.append(sym)
            seen_scores.add(count)
        if len(picks) >= MAX_FOLLOWUP_SUGGESTIONS:
            break

    # Build the question
    if picks:
        disease_hints = [d["disease_name"] for d in top[:2]]
        question = (
            f"Basado en lo que me dices, podría ser {disease_hints[0]}"
            f"{', ' + disease_hints[1] if len(disease_hints) > 1 else ''}. "
            f"¿Presenta también alguno de estos síntomas?"
        )
    else:
        question = "¿Podrías darme más detalles sobre los síntomas?"
        picks = []

    return {
        "question": question,
        "suggestions": picks,
        "diagnoses": results,
        "ready": False,
    }
