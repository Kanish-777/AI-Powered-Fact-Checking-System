SOURCE_WEIGHTS = {
    "Wikipedia": 0.85,
    "Government": 1.00,
    "Scientific": 1.00,
    "News": 0.80,
    "Unknown": 0.50
}


def get_source_credibility(source: str) -> float:
    return SOURCE_WEIGHTS.get(
        source,
        SOURCE_WEIGHTS["Unknown"]
    )