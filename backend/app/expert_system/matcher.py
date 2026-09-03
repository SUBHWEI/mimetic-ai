import math
import unicodedata


def _norm(s: str) -> str:
    """Lowercase, strip whitespace and remove accents for robust matching.

    Patients (and the UI) often type symptoms without diacritics ("vomito"
    instead of "vómito"); using accent-folded keys makes the matcher tolerant.
    """
    s = s.strip().lower()
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def build_symptom_weights(diseases: list[dict]) -> dict[str, float]:
    """Compute an Inverse Document Frequency (IDF)-like weight per symptom.

    Symptoms shared by very few diseases (specific/cardinal) get a high weight;
    symptoms present across many diseases (generic like "fatiga") get a low
    weight. This lets the matcher reward distinctive symptoms over vague ones.
    """
    n_diseases = len(diseases)
    if n_diseases == 0:
        return {}

    doc_freq: dict[str, int] = {}
    for disease in diseases:
        seen = set()
        for s in disease.get("symptoms", []):
            sym = _norm(s)
            if sym and sym not in seen:
                seen.add(sym)
                doc_freq[sym] = doc_freq.get(sym, 0) + 1

    # Compute raw IDF: log(N / df). Rare symptoms (low df) get high raw.
    raw_weights: dict[str, float] = {}
    for sym, count in doc_freq.items():
        raw_weights[sym] = math.log(n_diseases / count) if count > 0 else 0.0

    # Normalize linearly across the observed range so the rarest symptom maps
    # to max_w and the most common maps to min_w. This gives real separation
    # between cardinal and generic symptoms.
    max_raw = max(raw_weights.values()) if raw_weights else 1.0
    min_raw = min(raw_weights.values()) if raw_weights else 0.0
    span = (max_raw - min_raw) or 1.0

    min_w, max_w = 0.5, 2.0
    weights: dict[str, float] = {}
    for sym, raw in raw_weights.items():
        norm = (raw - min_raw) / span
        val = min_w + norm * (max_w - min_w)
        weights[sym] = round(val, 3)

    return weights


def calculate_match(
    symptoms_input: list[str],
    disease_symptoms: list[str],
    weights: dict[str, float] | None = None,
) -> tuple[int, float]:
    input_set = set(_norm(s) for s in symptoms_input)
    disease_set = set(_norm(d) for d in disease_symptoms)

    if not input_set or not disease_set:
        return 0, 0.0

    matches = input_set & disease_set
    matched_count = len(matches)

    if matched_count == 0:
        return 0, 0.0

    if weights:
        # Weighted score:
        #  - spec   = weighted fraction of the patient's symptoms that the
        #             disease has (rewards matching cardinal symptoms).
        #  - comp   = weighted fraction of the disease's symptoms covered.
        # Using sqrt(comp) softens the penalty for missing symptoms (patients
        # rarely present every symptom), so a strong pairwise match isn't
        # crushed by a long disease symptom list.
        matched_weight = sum(weights.get(m, 1.0) for m in matches)
        input_weight = sum(weights.get(m, 1.0) for m in input_set)
        disease_weight = sum(weights.get(m, 1.0) for m in disease_set)

        if input_weight <= 0 or disease_weight <= 0:
            score = 0.0
        else:
            spec = matched_weight / input_weight
            comp = matched_weight / disease_weight
            score = round(min(spec * math.sqrt(comp), 1.0), 2)
    else:
        # Fallback: plain ratio × coverage (backward compatible)
        ratio = matched_count / len(input_set)
        coverage = matched_count / len(disease_set) if disease_set else 0
        score = round(min(ratio * coverage * 1.5, 1.0), 2)

    return matched_count, score
