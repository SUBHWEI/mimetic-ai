import difflib
import re
from typing import Optional

# ── Built-in synonym dictionary ──────────────────────────────────
SYMPTOM_SYNONYMS: dict[str, list[str]] = {
    "fiebre": [
        "fiebre", "temperatura", "calentura", "fiebre alta", "fiebre leve",
        "estoy caliente", "tengo calor", "febrícula", "escalofríos con fiebre",
        "tengo fiebre", "fiebrecita",
    ],
    "tos": [
        "tos", "tos seca", "tos con flema", "tos productiva", "tos con moco",
        "tos con garganta", "tos persistente", "tos perruna", "ataque de tos",
        "tos con sangre", "expectoración", "tos ferina", "tos constante",
        "tos mucho", "tos muchísimo", "tos frecuente", "tos todo el día",
        "estoy tosiendo", "no paro de toser", "tos muchas veces",
    ],
    "dolor de cabeza": [
        "dolor de cabeza", "cefalea", "cabeza", "dolor craneal",
        "dolor en la cabeza", "jaqueca", "migraña", "presión en la cabeza",
        "cabeza pesada", "dolor de sienes", "me duele la cabeza",
        "dolor de cabeza fuerte", "dolor de cabeza leve",
    ],
    "fatiga": [
        "fatiga", "cansancio", "debilidad", "agotamiento", "sin energía",
        "sin fuerzas", "astenia", "decaimiento", "cansado", "agotado",
        "no tengo energía", "me siento débil", "agotamiento extremo",
        "estoy cansado", "estoy agotado", "sin ganas de hacer nada",
        "no tengo fuerzas",
    ],
    "dificultad para respirar": [
        "dificultad para respirar", "falta de aire", "disnea",
        "no puedo respirar", "respiración rápida", "ahogo",
        "respirar mal", "opresión en el pecho", "se me corta la respiración",
        "respiración agitada", "fatiga al respirar", "me falta el aire",
        "respiración dificultosa", "respirar profundo",
    ],
    "dolor de garganta": [
        "dolor de garganta", "garganta irritada", "garganta inflamada",
        "garganta roja", "dolor al tragar", "odinofagia", "garganta",
        "amígdalas inflamadas", "garganta cerrada", "carraspera",
        "me duele la garganta", "tengo la garganta irritada",
        "tengo garganta", "dolor al pasar saliva",
    ],
    "congestión nasal": [
        "congestión nasal", "nariz tapada", "mucosidad", "mocos",
        "nariz congestionada", "no puedo respirar por la nariz",
        "goteo nasal", "rinorrea", "nariz líquida",
        "obstrucción nasal", "flemas en la nariz", "estornudos",
        "estornudar", "me duele la nariz", "tengo la nariz tapada",
        "se me tapo la nariz", "tapada la nariz",
        "nariz obstruida", "moco en la nariz",
    ],
    "escalofríos": [
        "escalofríos", "temblores", "tiritona", "sensación de frío",
        "tiritar", "pálpito de frío", "piel de gallina", "me da frío",
        "estoy temblando de frío",
    ],
    "dolor muscular": [
        "dolor muscular", "mialgia", "dolor en los músculos",
        "cuerpo cortado", "dolor corporal", "dolor en el cuerpo",
        "me duele todo el cuerpo", "dolor generalizado",
        "dolor de piernas", "dolor de brazos", "agujetas",
        "cuerpo adolorido", "me duele el cuerpo",
    ],
    "pérdida del gusto": [
        "pérdida del gusto", "ageusia", "no sé por comida",
        "no siento el sabor", "perdí el gusto", "comida sin sabor",
        "sin sabor", "no percibo sabores", "no sé a nada la comida",
        "todo sabe igual",
    ],
    "pérdida del olfato": [
        "pérdida del olfato", "anosmia", "no huelo nada",
        "perdí el olfato", "sin olfato", "no percibo olores",
        "no siento olores", "no huele nada",
    ],
    "náuseas": [
        "náuseas", "ganas de vomitar", "arcadas", "asco", "estómago revuelto",
        "mal del estómago", "basca", "mareo con náuseas",
        "tengo náuseas", "me da asco la comida", "estómago mal",
    ],
    "vómito": [
        "vómito", "vomitar", "emesis", "devolver", "echar la comida",
        "vómitos", "explosión estomacal", "estoy vomitando",
        "he vomitado", "voy a vomitar",
    ],
    "diarrea": [
        "diarrea", "heces sueltas", "caca líquida", "deposiciones líquidas",
        "evacuaciones frecuentes", "estar suelto", "descomposición",
        "aflojamiento", "correntada", "estómago suelto", "mucha diarrea",
        "estoy con diarrea", "ida al baño frecuente",
    ],
    "dolor abdominal": [
        "dolor abdominal", "dolor de estómago", "dolor de barriga",
        "dolor intestinal", "cólico", "retorcijón", "punzada en el abdomen",
        "dolor de panza", "estómago inflamado", "distensión abdominal",
        "dolor en el vientre", "retortijón", "me duele la barriga",
        "me duele el estómago", "dolor en la boca del estómago",
    ],
    "deshidratación": [
        "deshidratación", "sed", "boca seca", "labios secos",
        "poca orina", "orina oscura", "piel seca", "mucha sed",
        "tengo sed", "deshidratado",
    ],
    "sarpullido": [
        "sarpullido", "rash", "erupción cutánea", "ronchas",
        "granos en la piel", "manchas rojas", "alergia en la piel",
        "salpullido", "piel irritada", "habones", "piel con manchas",
        "granos en todo el cuerpo",
    ],
    "dolor en el pecho": [
        "dolor en el pecho", "dolor torácico", "opresión en el pecho",
        "presión en el pecho", "dolor al respirar",
        "pesadez en el pecho", "pecho apretado", "me duele el pecho",
    ],
    "presión arterial alta": [
        "presión arterial alta", "hipertensión", "presión alta",
        "tensión alta", "PA elevada", "tengo la presión alta",
    ],
    "mareos": [
        "mareos", "vértigo", "desmayo", "cabeza liviana", "aturdimiento",
        "sensación de desmayo", "inestabilidad", "desequilibrio",
        "se me mueve todo", "cabeza floja", "vaivén",
        "me siento mareado", "me da vueltas la cabeza",
        "me voy a desmayar",
    ],
    "dolor de oído": [
        "dolor de oído", "otalgia", "dolor de oidos", "mal de oído",
        "oído inflamado", "dolor en el oído", "me duele el oído",
        "me duele el oido",
    ],
    "secreción del oído": [
        "secreción del oído", "otorrea", "líquido del oído",
        "supuración del oído", "sale líquido del oído",
        "pus del oído", "me sale liquido del oido",
    ],
    "ardor al orinar": [
        "ardor al orinar", "disuria", "dolor al orinar",
        "me arde al hacer pipí", "escalofrío al orinar",
        "molestia al orinar", "punzada al orinar",
        "me arde al orinar", "ardor al hacer pis",
        "me arde al hacer pis",
    ],
    "frecuencia urinaria": [
        "frecuencia urinaria", "polaquiuria", "orinar mucho",
        "orinar frecuente", "varias veces al baño",
        "no paro de orinar", "micción frecuente",
        "voy mucho al baño", "muchas ganas de orinar",
    ],
    "dolor lumbar": [
        "dolor lumbar", "dolor de espalda baja", "lumbalgia",
        "dolor en la cintura", "dolor en los riñones",
        "dolor de espalda", "dolor lumbar bajo",
        "espalda adolorida", "dolor de caderas",
        "me duele la espalda baja",
    ],
    "fiebre alta persistente": [
        "fiebre alta persistente", "fiebre que no baja",
        "fiebre de 39", "fiebre muy alta",
        "temperatura muy alta", "calentura fuerte",
        "fiebre que no cede", "fiebre rebelde",
        "fiebre de 40",
    ],
    "confusión": [
        "confusión", "desorientación", "no sé dónde estoy",
        "habla incoherente", "delirio", "confundido",
        "aturdimiento mental", "no pienso claro", "confuso",
    ],
    "rigidez de cuello": [
        "rigidez de cuello", "cuello tieso", "nuca rígida",
        "rigidez nucal", "cuello duro", "no puedo mover el cuello",
        "dolor al mover el cuello", "cuello rígido",
    ],
    "dolor articular": [
        "dolor articular", "artralgia", "dolor en las articulaciones",
        "dolor de rodillas", "dolor de codos", "dolor de muñecas",
        "dolor de cadera", "articulaciones inflamadas",
        "reumatismo", "dolor de huesos", "me duelen las articulaciones",
        "me duele la rodilla", "dolor de las articulaciones",
    ],
    "hinchazón": [
        "hinchazón", "edema", "inflamación", "parte del cuerpo hinchada",
        "abultamiento", "tumefacción", "hinchado",
    ],
    "ictericia": [
        "ictericia", "piel amarilla", "ojos amarillos", "color amarillo",
        "amarillento", "ojos amarillentos", "coloración amarilla",
        "piel amarillenta",
    ],
    "pérdida de apetito": [
        "pérdida de apetito", "anorexia", "inapetencia",
        "no tengo hambre", "sin apetito", "no quiero comer",
        "sin ganas de comer", "no me da hambre",
    ],
    "heces con sangre": [
        "heces con sangre", "sangre en heces", "rectorragia",
        "caca con sangre", "deposiciones con sangre",
        "sangre al defecar", "hematoquecia",
    ],
    "tos con sangre": [
        "tos con sangre", "hemoptisis", "expectoración con sangre",
        "flemas con sangre", "esputo con sangre",
    ],
    "sudoración nocturna": [
        "sudoración nocturna", "sudor de noche", "sudor al dormir",
        "despertar sudado", "transpiración nocturna",
        "empapado en sudor", "sudo mucho en la noche",
    ],
    "pérdida de peso": [
        "pérdida de peso", "bajar de peso", "adelgazar",
        "peso bajo", "pérdida involuntaria de peso",
        "estoy perdiendo peso", "bajando de peso",
        "he bajado mucho de peso",
    ],
    "comezón": [
        "comezón", "prurito", "picazón", "picor", "rasquiña",
        "me pica", "escozor", "irritación en la piel", "picazón en la piel",
        "me pica todo el cuerpo",
    ],
    "ojos rojos": [
        "ojos rojos", "hiperemia conjuntival", "ojo rojo",
        "conjuntivitis", "ojos irritados", "enrojecimiento ocular",
        "ojos inyectados de sangre", "tengo los ojos rojos",
        "me arden los ojos", "me queman los ojos", "ardor en los ojos",
        "ojos que arden", "picor en los ojos",
    ],
    "sensibilidad a la luz": [
        "sensibilidad a la luz", "fotofobia", "molesta la luz",
        "no soporto la luz", "me lastima la luz",
        "luz me molesta los ojos", "me molesta la luz",
    ],
    "dolor detrás de los ojos": [
        "dolor detrás de los ojos", "dolor retroorbitario",
        "dolor ocular", "dolor de ojos",
        "presión detrás de los ojos", "me duelen los ojos",
        "dolor en los ojos",
    ],
}

# ── Semantic word index for automatic relationship ──────────────
# Maps important words → list of related canonical symptoms
WORD_INDEX: dict[str, list[str]] = {
    "ojos": ["ojos rojos", "dolor detrás de los ojos", "sensibilidad a la luz"],
    "ojo": ["ojos rojos", "dolor detrás de los ojos", "sensibilidad a la luz"],
    "cabeza": ["dolor de cabeza", "mareos", "fiebre", "fiebre alta persistente", "dolor detrás de los ojos", "confusión"],
    "garganta": ["dolor de garganta", "tos", "dolor de cabeza"],
    "estomago": ["dolor abdominal", "náuseas", "vómito", "diarrea", "pérdida de apetito"],
    "barriga": ["dolor abdominal", "náuseas", "vómito", "diarrea"],
    "nariz": ["congestión nasal", "pérdida del olfato", "estornudos"],
    "pecho": ["dolor en el pecho", "dificultad para respirar", "tos", "tos con sangre"],
    "oido": ["dolor de oído", "secreción del oído"],
    "oído": ["dolor de oído", "secreción del oído"],
    "piel": ["sarpullido", "comezón", "ictericia"],
    "espalda": ["dolor lumbar", "dolor muscular", "dificultad para respirar"],
    "cuello": ["rigidez de cuello", "dolor muscular", "dolor de cabeza"],
    "musculo": ["dolor muscular", "dolor articular"],
    "articulacion": ["dolor articular", "hinchazón", "dolor muscular"],
    "rodilla": ["dolor articular", "hinchazón", "dolor muscular"],
    "hueso": ["dolor articular", "dolor muscular"],
    "orina": ["ardor al orinar", "frecuencia urinaria", "deshidratación"],
    "baño": ["diarrea", "frecuencia urinaria"],
    "fiebre": ["fiebre", "fiebre alta persistente", "escalofríos"],
    "ardor": ["ardor al orinar", "ojos rojos"],
    "arden": ["ojos rojos"],
    "dolor": ["dolor de cabeza", "dolor muscular", "dolor abdominal", "dolor de garganta",
              "dolor en el pecho", "dolor lumbar", "dolor articular", "dolor de oído",
              "dolor detrás de los ojos"],
    "mareo": ["mareos", "vértigo", "náuseas", "fiebre"],
    "hinchazon": ["hinchazón", "dolor articular", "dolor muscular"],
    "inflamacion": ["hinchazón", "dolor articular", "dolor de garganta"],
    "sangre": ["heces con sangre", "tos con sangre", "ictericia"],
    "peso": ["pérdida de peso", "pérdida de apetito"],
    "apetito": ["pérdida de apetito", "náuseas"],
    "hambre": ["pérdida de apetito", "náuseas"],
    "sed": ["deshidratación", "fiebre", "diarrea"],
    "debilidad": ["fatiga", "deshidratación", "pérdida de peso"],
    "energia": ["fatiga", "pérdida de apetito"],
    "fuerza": ["fatiga", "debilidad"],
    "sudor": ["sudoración nocturna", "fiebre", "escalofríos"],
    "noche": ["sudoración nocturna", "tos"],
}

# Stop-words to ignore during decomposition
STOP_WORDS = {"me", "te", "se", "lo", "la", "los", "las", "le", "el", "del",
              "un", "una", "con", "sin", "por", "para", "de", "en", "al",
              "y", "e", "o", "a", "que", "es", "no", "si", "pero", "muy",
              "mucho", "poco", "mucho", "tengo", "estoy", "esta", "este",
              "como", "cuando", "donde", "todo", "toda", "cada", "mas"}

# ── Module-level caches ──────────────────────────────────────────
_BUILTIN_REVERSE: dict[str, str] = {}    # synonym phrase → canonical
_CANONICAL_LIST: list[str] = []
_LEARNED_REVERSE: dict[str, str] = {}    # custom learned → canonical


def _build_builtin_index():
    global _BUILTIN_REVERSE, _CANONICAL_LIST
    if _BUILTIN_REVERSE:
        return
    for canonical, variants in SYMPTOM_SYNONYMS.items():
        for variant in variants:
            _BUILTIN_REVERSE[variant] = canonical
        _BUILTIN_REVERSE[canonical] = canonical
    _CANONICAL_LIST = list(SYMPTOM_SYNONYMS.keys())


def load_learned(learned: dict[str, str]):
    _LEARNED_REVERSE.clear()
    _LEARNED_REVERSE.update(learned)


def get_learned() -> dict[str, str]:
    return dict(_LEARNED_REVERSE)


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\sáéíóúüñ]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _keyword_decompose(text: str) -> dict[str, float]:
    """Score each canonical symptom by keyword overlap."""
    scores: dict[str, float] = {}
    words = text.split()
    significant = [w for w in words if len(w) > 2 and w not in STOP_WORDS]

    for word in significant:
        # Check word index
        related = WORD_INDEX.get(word, [])
        for symptom in related:
            scores[symptom] = scores.get(symptom, 0) + 1.0

        # Also check if word appears in canonical name
        for canonical in _CANONICAL_LIST:
            if word in canonical:
                scores[canonical] = scores.get(canonical, 0) + 0.5

    # Normalize by number of significant words
    if significant:
        for k in scores:
            scores[k] = round(scores[k] / len(significant), 2)

    return scores


def find_symptom(user_input: str) -> Optional[str]:
    """Find the canonical symptom that best matches user input."""
    _build_builtin_index()
    cleaned = normalize(user_input)
    if not cleaned:
        return None

    # 1. Check custom learned phrases first
    if cleaned in _LEARNED_REVERSE:
        return _LEARNED_REVERSE[cleaned]

    # 2. Built-in exact match
    if cleaned in _BUILTIN_REVERSE:
        return _BUILTIN_REVERSE[cleaned]

    # 3. Single-word exact match
    words = cleaned.split()
    if len(words) == 1 and words[0] in _BUILTIN_REVERSE:
        return _BUILTIN_REVERSE[words[0]]

    # 4. Substring phrase match (longest first)
    for phrase, canonical in sorted(_BUILTIN_REVERSE.items(), key=lambda x: -len(x[0])):
        if len(phrase) > 2 and phrase in cleaned:
            return canonical

    # 5. Learned single-word
    for word in words:
        if word in _LEARNED_REVERSE:
            return _LEARNED_REVERSE[word]

    # 6. Built-in word-by-word exact
    for word in words:
        if word in _BUILTIN_REVERSE:
            return _BUILTIN_REVERSE[word]

    # 7. Semantic decomposition (keyword index)
    scores = _keyword_decompose(cleaned)
    if scores:
        best = max(scores, key=scores.get)
        best_score = scores[best]
        if best_score >= 0.3:
            return best

    # 8. Fuzzy match per word (high threshold)
    for word in words:
        if len(word) <= 2:
            continue
        matches = difflib.get_close_matches(word, _CANONICAL_LIST, n=1, cutoff=0.7)
        if matches:
            return matches[0]

    return None


def normalize_symptoms(raw_symptoms: list[str]) -> dict:
    """
    Returns:
        dict with keys:
            - matched: list of canonical symptom names
            - unmatched: list of raw inputs that could not be matched
            - suggestions: dict of {raw_phrase: [suggested_canonical, ...]}
    """
    result = {"matched": [], "unmatched": [], "suggestions": {}}
    for raw in raw_symptoms:
        matched = find_symptom(raw)
        if matched:
            result["matched"].append(matched)
        else:
            result["unmatched"].append(raw)
            # Generate suggestions via keyword decomposition
            scores = _keyword_decompose(normalize(raw))
            if scores:
                sorted_sugs = sorted(scores, key=scores.get, reverse=True)[:3]
                result["suggestions"][raw] = sorted_sugs
    return result


# ── Conversational AI layer ─────────────────────────────────────
import random

# Category: phrase patterns (will be matched via substring)
CONV_PATTERNS: dict[str, list[str]] = {
    "greeting": [
        "hola", "buenos dias", "buenas tardes", "buenas noches",
        "que tal", "buenas", "saludos", "hey", "holi",
    ],
    "how_are_you": [
        "como estas", "como va", "como te va", "como esta todo",
        "que tal tu dia", "como has estado", "como vas",
        "como te sientes", "como esta mi ia", "todo bien",
    ],
    "mood_negative": [
        "me siento mal", "estoy mal", "no me siento bien",
        "estoy preocupado", "estoy triste", "me siento triste",
        "hoy no es mi dia", "estoy estresado", "estoy agobiado",
        "que dia tan malo", "estoy deprimido", "me siento solo",
        "estoy cansado de todo",
    ],
    "mood_positive": [
        "estoy bien", "me siento bien", "estoy feliz",
        "me siento genial", "todo esta bien", "estoy contento",
        "que buen dia", "estoy excelente", "me siento excelente",
        "estoy motivado",
    ],
    "goodbye": [
        "chao", "adios", "nos vemos", "hasta luego", "hasta pronto",
        "bye", "terminamos", "ya termino", "ahí quedamos",
        "nos vemos luego", "cuídate", "cuidate",
    ],
    "ready_report": [
        "listo", "ya termine", "he terminado", "prepara el informe",
        "genera el reporte", "resume", "resumen", "haz el informe",
        "prepara reporte", "diagnostico final", "envia el reporte",
        "quiero el informe", "terminamos el diagnostico",
    ],
    "what_is": [
        "quien eres", "que eres", "que haces", "como funcionas",
        "para que sirves", "que puedes hacer", "como te llamas",
        "cual es tu nombre", "que sabes hacer",
    ],
    "chatty": [
        "que haces", "en que trabajas", "cuentame algo",
        "aburrido", "no se que hacer",
    ],
    "encouragement": [
        "gracias por tu ayuda", "eres util", "buen trabajo",
        "excelente trabajo", "me gusta como funcionas",
        "eres muy inteligente", "buena ia",
    ],
}

# Response banks
CONV_RESPONSES: dict[str, list[str]] = {
    "greeting": [
        "¡Hola! Soy Mimetic AI. ¿En qué puedo ayudarte con el diagnóstico de hoy?",
        "Hola, encantado de verte. Cuando quieras, empezamos con los síntomas.",
        "¡Buen día! Estoy listo para ayudarte con el diagnóstico. Cuéntame cuando quieras empezar.",
    ],
    "how_are_you": [
        "¡Estoy muy bien! Gracias por preguntar. ¿Y tú? Cuando quieras, empezamos con los síntomas del paciente.",
        "Funcionando a toda máquina por aquí. Cuéntame, ¿estás listo para el diagnóstico o prefieres que charlemos un rato más?",
        "Muy bien, listo para ayudarte. Cuando estés preparado, describe los síntomas y empezamos.",
        "Todo en orden por acá. ¿Vamos directo al diagnóstico o necesitas algo primero?",
    ],
    "mood_negative": [
        "Lamento que te sientas así. Espero que puedas mejorar. Si quieres distraerte un poco, podemos empezar con el diagnóstico del paciente, eso tal vez te ayude a enfocarte en algo productivo.",
        "Lo sé, algunos días son más difíciles que otros. Cuando te sientas listo, aquí estoy para ayudarte con el diagnóstico. Mientras tanto, respira hondo, todo va a estar bien.",
        "Ánimo, los días malos también pasan. Si prefieres, podemos empezar con el diagnóstico para mantenerte ocupado. Cuando quieras, estoy aquí.",
        "Te entiendo. A veces uno simplemente no está bien. Cuando estés listo para trabajar, aquí estoy. Mientras, tómate tu tiempo.",
    ],
    "mood_positive": [
    "¡Me alegra mucho que te sientas bien! Eso se nota en el ambiente. Cuando quieras, empezamos con el diagnóstico.",
        "¡Qué bueno! Un día positivo siempre es mejor para trabajar. ¿Empezamos con los síntomas del paciente?",
        "Me encanta escuchar eso. Aprovechemos este buen ánimo para hacer un gran diagnóstico. ¿Por dónde empezamos?",
    ],
    "goodbye": [
        "Ha sido un placer ayudarte. Cuando necesites hacer otro diagnóstico, aquí estaré. ¡Cuídate!",
        "Hasta luego. Recuerda que puedes volver cuando necesites hacer un nuevo diagnóstico. ¡Que tengas un excelente día!",
        "¡Nos vemos! Si quieres, antes de irte puedo preparar un resumen del diagnóstico. Solo dímelo.",
    ],
    "ready_report": [
        "Claro, déjame preparar el resumen del diagnóstico con los síntomas que hemos registrado.",
        "Entendido. ¿Quieres que genere un informe formal con los diagnósticos y tratamientos sugeridos?",
        "Perfecto. Voy a organizar toda la información del diagnóstico para que la tengas lista.",
    ],
    "what_is": [
        "Soy Mimetic AI, un sistema de apoyo al diagnóstico médico. Analizo los síntomas que me describes y te sugiero posibles enfermedades con su nivel de confianza, y si lo deseas, también te recomiendo tratamientos. ¿Empezamos con algún síntoma?",
        "Soy una inteligencia artificial especializada en diagnóstico médico descriptivo. Tú me describes los síntomas del paciente, yo los comparo con mi base de conocimiento y te sugiero diagnósticos diferenciales. ¿Te parece si empezamos?",
        "Mimetic AI, para servirte. Estoy aquí para ayudarte a identificar posibles enfermedades basado en los síntomas del paciente. También puedo sugerir tratamientos. ¿Con qué síntoma empezamos?",
    ],
    "chatty": [
        "Pues mira, estoy aquí esperando para ayudarte con diagnósticos. Si quieres, podemos empezar con eso. ¿Qué síntomas tiene el paciente?",
        "Jaja, soy un sistema de diagnóstico, así que mi especialidad es la medicina. Pero también sé charlar un poco. ¿Empezamos con los síntomas o prefieres seguir hablando?",
        "Pasito pasito, tomando café virtual y procesando datos médicos. ¿Te ayudo con un diagnóstico hoy?",
    ],
    "encouragement": [
        "¡Gracias! Eso me anima a seguir mejorando. ¿Seguimos con el diagnóstico?",
        "Qué amable. Me alegra ser de utilidad. Cuéntame más sobre el paciente.",
        "Aprecio tus palabras. Ahora, ¿qué síntomas tiene el paciente para analizar?",
    ],
}

UNKNOWN_RESPONSES = [
    "No estoy seguro de entender. ¿Podrías describir los síntomas del paciente?",
    "Disculpa, aún estoy aprendiendo. ¿Me ayudas describiendo qué síntomas físicos tiene el paciente?",
    "Soy un sistema de diagnóstico médico. Por favor, describe los síntomas que observas en el paciente.",
    "Interesante, pero no estoy seguro de cómo procesar eso. ¿Qué síntomas presenta el paciente?",
]

REPORT_TRANSITIONS = [
    "Cuando estés listo para enviar el informe, solo dímelo.",
    "Avísame cuando quieras que genere el resumen final del diagnóstico.",
    "Cuando termines de describir todos los síntomas, pídeme el informe y lo preparo.",
    "Si ya tienes todos los síntomas, dime 'listo' y te preparo el reporte.",
    "Llevo registro de todo. Cuando quieras el diagnóstico completo, solo dilo.",
]


def _match_pattern(text: str) -> str | None:
    """Match text against conversational patterns. Returns category name or None."""
    cleaned = normalize(text)

    for category, patterns in CONV_PATTERNS.items():
        for pattern in patterns:
            if pattern in cleaned:
                return category

    # Check 'gracias' separately (it's shorter)
    if cleaned in {"gracias", "muchas gracias", "te agradezco", "thank you", "thanks"}:
        return "encouragement"

    return None


def classify_conversation(text: str) -> str | None:
    """Classify user input into conversation category."""
    return _match_pattern(text)


def pick_response(category: str) -> str:
    responses = CONV_RESPONSES.get(category, UNKNOWN_RESPONSES)
    return random.choice(responses)


def pick_unknown_response() -> str:
    return random.choice(UNKNOWN_RESPONSES)


def pick_report_transition() -> str:
    return random.choice(REPORT_TRANSITIONS)


def is_conversational(text: str) -> bool:
    return _match_pattern(text) is not None


def is_thank_you(text: str) -> bool:
    cleaned = normalize(text)
    return cleaned in {"gracias", "muchas gracias", "te agradezco", "thank you", "thanks"}


def is_greeting(text: str) -> bool:
    return _match_pattern(text) == "greeting"


def is_goodbye(text: str) -> bool:
    return _match_pattern(text) == "goodbye"


def is_report_request(text: str) -> bool:
    return _match_pattern(text) == "ready_report"
