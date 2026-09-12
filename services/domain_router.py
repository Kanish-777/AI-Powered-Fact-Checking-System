HEALTH_KEYWORDS = {
    "cancer",
    "disease",
    "health",
    "medical",
    "medicine",
    "drug",
    "drugs",
    "vaccine",
    "vaccines",
    "virus",
    "viral",
    "bacteria",
    "bacterial",
    "infection",
    "smoking",
    "tobacco",
    "coffee",
    "caffeine",
    "blood",
    "heart",
    "brain",
    "lung",
    "lungs",
    "diabetes",
    "obesity",
    "cholesterol",
    "protein",
    "vitamin",
    "diet",
    "exercise",
    "depression",
    "anxiety",
    "mortality",
    "treatment",
    "therapy",
    "symptom",
    "symptoms",
    "covid",
    "coronavirus",
    "hypertension",
    "alzheimer",
    "stroke"
}


HEALTH_PHRASES = {
    "risk of",
    "increases risk",
    "reduces risk",
    "causes cancer",
    "mental health",
    "heart disease",
    "blood pressure",
    "clinical trial",
    "side effects"
}


def detect_claim_domain(
    claim: str
) -> str:

    normalized_claim = claim.lower()

    words = set(
        normalized_claim
        .replace(".", " ")
        .replace(",", " ")
        .replace("?", " ")
        .replace("!", " ")
        .split()
    )

    if words.intersection(
        HEALTH_KEYWORDS
    ):
        return "HEALTH"

    for phrase in HEALTH_PHRASES:

        if phrase in normalized_claim:
            return "HEALTH"

    return "GENERAL"


def should_use_scientific_source(
    claim: str
) -> bool:

    return (
        detect_claim_domain(claim)
        == "HEALTH"
    )