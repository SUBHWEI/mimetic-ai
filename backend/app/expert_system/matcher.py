def calculate_match(symptoms_input: list[str], disease_symptoms: list[str]) -> tuple[int, float]:
    input_set = set(s.lower().strip() for s in symptoms_input)
    disease_set = set(d.lower().strip() for d in disease_symptoms)

    if not input_set or not disease_set:
        return 0, 0.0

    matches = input_set & disease_set
    matched_count = len(matches)
    total_possible = len(input_set)

    if matched_count == 0:
        return 0, 0.0

    # Ratio of matched symptoms vs total input symptoms
    ratio = matched_count / total_possible

    # Also consider what fraction of disease symptoms were matched
    coverage = matched_count / len(disease_set) if disease_set else 0

    # Combined score
    score = (ratio * 0.6) + (coverage * 0.4)
    score = round(min(score, 1.0), 2)

    return matched_count, score
