def calculate_match(symptoms_input: list[str], disease_symptoms: list[str]) -> tuple[int, float]:
    input_set = set(s.lower().strip() for s in symptoms_input)
    disease_set = set(d.lower().strip() for d in disease_symptoms)

    if not input_set or not disease_set:
        return 0, 0.0

    matches = input_set & disease_set
    matched_count = len(matches)

    if matched_count == 0:
        return 0, 0.0

    # Ratio of user's symptoms that match the disease
    ratio = matched_count / len(input_set)

    # Fraction of disease symptoms the user has (coverage)
    coverage = matched_count / len(disease_set) if disease_set else 0

    # Score = ratio × coverage, penalizing diseases where most of their
    # symptoms are NOT present in the user. Multiplied by 1.5 to
    # maintain similar scale as before for strong matches.
    score = round(min(ratio * coverage * 1.5, 1.0), 2)

    return matched_count, score
