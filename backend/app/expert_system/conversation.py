"""Conversational engine for interactive diagnosis."""

from app.expert_system.engine import diagnose
from app.database.mongodb import get_db

MAX_CANDIDATES_FOR_SUGGESTIONS = 5
TARGET_DIAGNOSES_COUNT = 3
MAX_FOLLOWUP_SUGGESTIONS = 4


def _prettify_symptom(raw: str) -> str:
    raw = raw.strip()
    if not raw.startswith("dolor "):
        return raw
    rest = raw[5:].strip()
    if rest.startswith("de "):
        rest = rest[3:].strip()
    if rest.startswith("en el "):
        rest = "el " + rest[6:].strip()
    elif rest.startswith("en la "):
        rest = "la " + rest[6:].strip()
    elif rest.startswith("en los "):
        rest = "los " + rest[7:].strip()
    elif rest.startswith("en las "):
        rest = "las " + rest[7:].strip()
    return f"Dolor de {rest}"


_SPECIFIC_QUESTIONS: dict[str, str] = {
    "fiebre": "¿Ha tenido fiebre?",
    "fiebre alta": "¿Ha tenido fiebre mayor a 39°C?",
    "fiebre alta persistente": "¿Ha tenido fiebre mayor a 39°C?",
    "tos": "¿Tiene tos?",
    "tos seca": "¿Tiene tos seca?",
    "tos con flema": "¿Tiene tos con flema?",
    "tos productiva": "¿Tiene tos con flema?",
    "dolor de cabeza": "¿El dolor de cabeza es pulsátil o de tipo opresivo?",
    "dolor de cabeza intenso": "¿El dolor de cabeza es pulsátil o de tipo opresivo?",
    "cefalea": "¿El dolor de cabeza es pulsátil o de tipo opresivo?",
    "dolor detras de los ojos": "¿Presenta dolor detrás de los ojos?",
    "dolor retroocular": "¿Presenta dolor detrás de los ojos?",
    "dolor de garganta": "¿Tiene dolor de garganta?",
    "dolor abdominal": "¿El dolor abdominal es tipo cólico o constante?",
    "dolor muscular": "¿Tiene dolor muscular generalizado?",
    "mialgia": "¿Tiene dolor muscular generalizado?",
    "dolor en las articulaciones": "¿Tiene dolor en las articulaciones?",
    "artralgia": "¿Tiene dolor en las articulaciones?",
    "rigidez en el cuello": "¿Tiene rigidez en el cuello?",
    "rigidez de nuca": "¿Tiene rigidez en el cuello?",
    "fatiga": "¿Se ha sentido fatigado o con cansancio extremo?",
    "debilidad": "¿Ha sentido debilidad generalizada?",
    "perdida del gusto": "¿Ha perdido el sentido del gusto?",
    "perdida del olfato": "¿Ha perdido el sentido del olfato?",
    "anosmia": "¿Ha perdido el sentido del olfato?",
    "ageusia": "¿Ha perdido el sentido del gusto?",
    "congestion nasal": "¿Tiene congestión nasal?",
    "secrecion nasal": "¿Tiene secreción nasal?",
    "rinorrea": "¿Tiene secreción nasal?",
    "estornudos": "¿Ha estado estornudando frecuentemente?",
    "dificultad para respirar": "¿Tiene dificultad para respirar?",
    "disnea": "¿Tiene dificultad para respirar?",
    "opresion en el pecho": "¿Siente opresión en el pecho?",
    "dolor en el pecho": "¿Siente dolor en el pecho?",
    "palpitaciones": "¿Ha sentido palpitaciones o taquicardia?",
    "nausea": "¿Ha tenido náuseas?",
    "nauseas": "¿Ha tenido náuseas?",
    "vomito": "¿Ha tenido vómitos?",
    "vómito": "¿Ha tenido vómitos?",
    "diarrea": "¿Ha tenido diarrea?",
    "escalofrios": "¿Ha tenido escalofríos?",
    "sudoracion": "¿Ha tenido sudoración excesiva?",
    "sudoracion nocturna": "¿Ha tenido sudoración nocturna?",
    "perdida de peso": "¿Ha perdido peso sin razón aparente?",
    "perdida del apetito": "¿Ha perdido el apetito?",
    "mareo": "¿Ha tenido mareos?",
    "vertigo": "¿Ha tenido vértigo?",
    "desmayo": "¿Se ha desmayado?",
    "sincope": "¿Se ha desmayado?",
    "erupcion cutanea": "¿Tiene erupción cutánea?",
    "rash": "¿Tiene erupción cutánea?",
    "picazon": "¿Tiene picazón en alguna parte del cuerpo?",
    "prurito": "¿Tiene picazón en alguna parte del cuerpo?",
    "hinchazon": "¿Tiene hinchazón en alguna parte del cuerpo?",
    "edema": "¿Tiene hinchazón en alguna parte del cuerpo?",
    "ictericia": "¿Tiene coloración amarillenta en la piel u ojos?",
    "orina oscura": "¿Tiene orina oscura?",
    "sangrado": "¿Ha tenido sangrado?",
    "moretones": "¿Le salen moretones con facilidad?",
    "fotofobia": "¿Tiene molestia a la luz?",
    "sensibilidad a la luz": "¿Tiene molestia a la luz?",
    "fonofobia": "¿Tiene molestia a los ruidos fuertes?",
}


def _build_specific_question(symptom_name: str) -> str | None:
    key = symptom_name.lower().strip()
    for pattern, question in _SPECIFIC_QUESTIONS.items():
        if pattern in key or key in pattern:
            return question
    return None


async def generate_followup(symptoms: list[str]) -> dict:
    """Generate follow-up question based on current symptoms.

    Always tries to ask discriminating questions first.
    Only returns ready=True when no more useful questions remain.

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

    top = results[:MAX_CANDIDATES_FOR_SUGGESTIONS]
    top_names = {d["disease_name"] for d in top}

    db = get_db()
    if db is None:
        return {"question": "", "suggestions": [], "diagnoses": results, "ready": True}

    disease_docs = await db.diseases.find(
        {"name": {"$in": list(top_names)}}
    ).to_list(length=None)

    # Map disease_name -> set of symptoms
    disease_symptoms_map: dict[str, set[str]] = {}
    for doc in disease_docs:
        name = doc["name"]
        disease_symptoms_map[name] = {
            s.lower().strip() for s in doc.get("symptoms", [])
        }

    already_mentioned = set(s.lower().strip() for s in symptoms)

    # --- Discriminating symptoms (unique to one top disease) ---
    discriminating: dict[str, list[str]] = {}
    for d_name in top_names:
        ds = disease_symptoms_map.get(d_name, set())
        others = set()
        for other_name in top_names:
            if other_name != d_name:
                others |= disease_symptoms_map.get(other_name, set())
        unique = ds - others - already_mentioned
        if unique:
            discriminating[d_name] = list(unique)

    # --- Useful shared symptoms (present in >= 2 top diseases but not mentioned) ---
    from collections import Counter
    shared_counter: Counter = Counter()
    for d_name in top_names:
        ds = disease_symptoms_map.get(d_name, set())
        for s in ds:
            if s not in already_mentioned:
                shared_counter[s] += 1

    shared_useful = [s for s, count in shared_counter.items() if count >= 2]
    shared_useful.sort(key=lambda s: -shared_counter[s])

    # --- Pick the best questions ---
    picks: list[str] = []
    questions_asked: list[str] = []

    # 1st priority: discriminating symptoms
    for d_name in top_names:
        for sym in discriminating.get(d_name, []):
            if len(picks) >= MAX_FOLLOWUP_SUGGESTIONS:
                break
            if sym not in picks:
                q = _build_specific_question(sym)
                if q and q not in questions_asked:
                    picks.append(sym)
                    questions_asked.append(q)

    # 2nd priority: fill remaining slots with useful shared symptoms
    for sym in shared_useful:
        if len(picks) >= MAX_FOLLOWUP_SUGGESTIONS:
            break
        if sym not in picks:
            q = _build_specific_question(sym)
            if q and q not in questions_asked:
                picks.append(sym)
                questions_asked.append(q)

    # 3rd priority: any remaining symptom from top diseases
    if len(picks) < MAX_FOLLOWUP_SUGGESTIONS:
        for d_name in top_names:
            for sym in disease_symptoms_map.get(d_name, set()):
                if len(picks) >= MAX_FOLLOWUP_SUGGESTIONS:
                    break
                if sym not in already_mentioned and sym not in picks:
                    picks.append(sym)
                    q = _build_specific_question(sym)
                    if q and q not in questions_asked:
                        questions_asked.append(q)

    # --- Determine if ready ---
    # Ready if: only 1 diagnosis, OR (<= TARGET diagnoses AND no questions to ask)
    is_ready = False
    if len(results) <= 1:
        is_ready = True
    elif len(results) <= TARGET_DIAGNOSES_COUNT and not questions_asked:
        is_ready = True

    if is_ready:
        return {
            "question": "",
            "suggestions": [],
            "diagnoses": results,
            "ready": True,
        }

    # --- Build the question text ---
    question = ""
    if questions_asked:
        question = questions_asked[0] + " "
        if len(picks) > 1:
            sym_texts = [_prettify_symptom(p) for p in picks[1:]]
            question += "Además, ¿presenta " + ", ".join(sym_texts) + "?"
        else:
            disease_hints = [d["disease_name"] for d in top[:3]]
            question += f"(Podría ser {' o '.join(disease_hints)})"
    else:
        disease_hints = [d["disease_name"] for d in top[:3]]
        question = (
            f"Basado en lo que me dices, podría ser {' o '.join(disease_hints)}. "
            "¿Podrías darme más detalles sobre los síntomas?"
        )

    return {
        "question": question,
        "suggestions": picks,
        "diagnoses": top,
        "ready": False,
    }
