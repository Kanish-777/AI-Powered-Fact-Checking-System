import re


COMPARISON_PATTERN = re.compile(
    r"^(?:the\s+)?(.+?)\s+is\s+"
    r"(larger|smaller|bigger|greater|"
    r"hotter|warmer|colder|cooler)\s+than\s+"
    r"(?:the\s+)?(.+?)[.!?]?$",
    flags=re.IGNORECASE
)


def normalize_text(text: str) -> str:

    text = (
        text.replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
    )

    return re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()


def detect_comparison_claim(
    claim: str
) -> dict | None:

    match = COMPARISON_PATTERN.match(
        claim.strip()
    )

    if not match:
        return None

    return {
        "subject": match.group(1).strip(),
        "relation": match.group(2).lower(),
        "object": match.group(3).strip()
    }


# ============================================================
# ENTITY TITLE MATCHING
# ============================================================

def title_matches_entity(
    entity: str,
    title: str
) -> bool:

    entity_normalized = normalize_text(
        entity
    )

    title_normalized = normalize_text(
        title
    )

    pattern = (
        rf"^{re.escape(entity_normalized)}"
        rf"(?:\s*\([^)]*\))?$"
    )

    return bool(
        re.fullmatch(
            pattern,
            title_normalized,
            flags=re.IGNORECASE
        )
    )


# ============================================================
# SENTENCE SPLITTING
# ============================================================

def split_sentences(
    text: str
) -> list[str]:

    return [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+",
            text
        )
        if sentence.strip()
    ]


# ============================================================
# NUMBER PARSING
# ============================================================

def parse_number(
    value: str
) -> float | None:

    try:

        normalized_value = (
            value
            .replace(",", "")
            .replace("−", "-")
            .replace("–", "-")
            .replace("—", "-")
        )

        return float(
            normalized_value
        )

    except ValueError:

        return None


# ============================================================
# AREA EXTRACTION
# ============================================================

def extract_area_values(
    text: str
) -> list[float]:

    values = []

    normalized = normalize_text(
        text
    )

    patterns = [
        r"([\d,]+(?:\.\d+)?)\s*km2\b",
        r"([\d,]+(?:\.\d+)?)\s*km²\b",
        r"([\d,]+(?:\.\d+)?)\s*square kilometers?\b",
        r"([\d,]+(?:\.\d+)?)\s*square kilometres?\b"
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            normalized,
            flags=re.IGNORECASE
        )

        for match in matches:

            number = parse_number(
                match
            )

            if number is not None:

                values.append(
                    number
                )

    return values


# ============================================================
# DIAMETER EXTRACTION
# ============================================================

def extract_diameter_values(
    text: str
) -> list[float]:

    values = []

    normalized = normalize_text(
        text
    )

    patterns = [
        (
            r"diameter"
            r"(?:\s+of|\s+is|\s+approximately|\s+about)?"
            r"\s*([\d,]+(?:\.\d+)?)\s*km\b"
        ),
        (
            r"([\d,]+(?:\.\d+)?)\s*km"
            r"(?:\s+in)?\s+diameter\b"
        )
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            normalized,
            flags=re.IGNORECASE
        )

        for match in matches:

            number = parse_number(
                match
            )

            if number is not None:

                values.append(
                    number
                )

    return values


# ============================================================
# RADIUS EXTRACTION
# ============================================================

def extract_radius_values(
    text: str
) -> list[float]:

    values = []

    normalized = normalize_text(
        text
    )

    patterns = [
        (
            r"(?:mean\s+|equatorial\s+|average\s+)?"
            r"radius"
            r"(?:\s+of|\s+is|\s+approximately|\s+about)?"
            r"\s*([\d,]+(?:\.\d+)?)\s*km\b"
        ),
        (
            r"([\d,]+(?:\.\d+)?)\s*km"
            r"(?:\s+in)?\s+radius\b"
        )
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            normalized,
            flags=re.IGNORECASE
        )

        for match in matches:

            number = parse_number(
                match
            )

            if number is not None:

                values.append(
                    number
                )

    return values


# ============================================================
# TEMPERATURE HELPERS
# ============================================================

def kelvin_to_celsius(
    kelvin: float
) -> float:

    return kelvin - 273.15


def is_extreme_temperature_sentence(
    text: str
) -> bool:

    normalized = normalize_text(
        text
    )

    extreme_patterns = [
        "lowest temperature",
        "highest temperature",
        "lowest natural temperature",
        "highest natural temperature",
        "recorded low",
        "recorded high",
        "record low",
        "record high",
        "temperature record",
        "coldest temperature",
        "hottest temperature"
    ]

    return any(
        pattern in normalized
        for pattern in extreme_patterns
    )


def has_preferred_temperature_context(
    text: str
) -> bool:

    normalized = normalize_text(
        text
    )

    preferred_patterns = [
        "average surface temperature",
        "mean surface temperature",
        "surface temperature averages",
        "surface temperature is",
        "surface temperature of",
        "average temperature",
        "mean temperature",
        "temperature averages",
        "true temperature",
        "actual temperature"
    ]

    return any(
        pattern in normalized
        for pattern in preferred_patterns
    )


def has_black_body_context(
    text: str
) -> bool:

    normalized = normalize_text(
        text
    )

    return (
        "black-body temperature" in normalized
        or "black body temperature" in normalized
        or "equilibrium temperature" in normalized
    )


def extract_temperature_values(
    text: str
) -> list[float]:

    normalized = normalize_text(
        text
    )

    # --------------------------------------------------------
    # Reject temperature records/extremes.
    #
    # Example:
    # "lowest temperature recorded on Earth = -89.2 °C"
    #
    # That is not comparable with Venus's average surface
    # temperature.
    # --------------------------------------------------------

    if is_extreme_temperature_sentence(
        normalized
    ):
        return []

    # --------------------------------------------------------
    # Reject black-body/equilibrium values unless the same
    # sentence also clearly gives actual/true/surface temp.
    # --------------------------------------------------------

    if has_black_body_context(
        normalized
    ):

        if not (
            "true temperature" in normalized
            or "actual temperature" in normalized
            or "surface temperature" in normalized
        ):
            return []

    values = []

    # --------------------------------------------------------
    # CELSIUS
    # --------------------------------------------------------

    celsius_patterns = [
        r"(-?\d+(?:\.\d+)?)\s*°\s*c\b",
        r"(-?\d+(?:\.\d+)?)\s*degrees?\s+celsius\b"
    ]

    for pattern in celsius_patterns:

        matches = re.findall(
            pattern,
            normalized,
            flags=re.IGNORECASE
        )

        for match in matches:

            number = parse_number(
                match
            )

            if number is not None:

                values.append(
                    number
                )

    # --------------------------------------------------------
    # KELVIN
    # --------------------------------------------------------

    kelvin_matches = re.findall(
        r"(-?\d+(?:\.\d+)?)\s*k\b",
        normalized,
        flags=re.IGNORECASE
    )

    for match in kelvin_matches:

        number = parse_number(
            match
        )

        if number is not None:

            celsius_value = (
                kelvin_to_celsius(
                    number
                )
            )

            if not any(
                abs(
                    existing
                    - celsius_value
                ) < 2.0
                for existing in values
            ):

                values.append(
                    celsius_value
                )

    return values


# ============================================================
# RANK EXTRACTION
# ============================================================

def detect_entity_rank(
    entity: str,
    sentence: str
) -> dict:

    normalized_sentence = normalize_text(
        sentence
    )

    entity_pattern = re.escape(
        normalize_text(
            entity
        )
    )

    result = {
        "largest": False,
        "second_largest": False,
        "smallest": False,
        "second_smallest": False
    }

    second_largest_pattern = (
        rf"\b{entity_pattern}\b"
        rf".{{0,100}}"
        rf"\b(?:is|was|remains|became)\b"
        rf".{{0,100}}"
        rf"\bsecond[-\s]largest\b"
    )

    largest_pattern = (
        rf"\b{entity_pattern}\b"
        rf".{{0,100}}"
        rf"\b(?:is|was|remains|became)\b"
        rf".{{0,100}}"
        rf"\b(?:the\s+)?largest\b"
    )

    second_smallest_pattern = (
        rf"\b{entity_pattern}\b"
        rf".{{0,100}}"
        rf"\b(?:is|was|remains|became)\b"
        rf".{{0,100}}"
        rf"\bsecond[-\s]smallest\b"
    )

    smallest_pattern = (
        rf"\b{entity_pattern}\b"
        rf".{{0,100}}"
        rf"\b(?:is|was|remains|became)\b"
        rf".{{0,100}}"
        rf"\b(?:the\s+)?smallest\b"
    )

    if re.search(
        second_largest_pattern,
        normalized_sentence
    ):

        result[
            "second_largest"
        ] = True

    elif re.search(
        largest_pattern,
        normalized_sentence
    ):

        result[
            "largest"
        ] = True

    if re.search(
        second_smallest_pattern,
        normalized_sentence
    ):

        result[
            "second_smallest"
        ] = True

    elif re.search(
        smallest_pattern,
        normalized_sentence
    ):

        result[
            "smallest"
        ] = True

    return result


# ============================================================
# ENTITY INFORMATION
# ============================================================

def find_entity_information(
    entity: str,
    evidence: list[dict]
) -> dict:

    entity_lower = normalize_text(
        entity
    )

    result = {
        "largest": False,
        "second_largest": False,
        "smallest": False,
        "second_smallest": False,

        "area_values": [],
        "diameter_values": [],
        "radius_values": [],

        "preferred_temperature_values": [],
        "fallback_temperature_values": []
    }

    for item in evidence:

        title = item.get(
            "title",
            ""
        )

        raw_text = item.get(
            "text",
            ""
        )

        search_query = normalize_text(
            item.get(
                "search_query",
                ""
            )
        )

        exact_title_match = (
            title_matches_entity(
                entity,
                title
            )
        )

        query_match = (
            entity_lower
            in search_query
        )

        if not (
            exact_title_match
            or query_match
        ):

            continue

        sentences = split_sentences(
            raw_text
        )

        for sentence in sentences:

            normalized_sentence = normalize_text(
                sentence
            )

            if (
                entity_lower
                in normalized_sentence
            ):

                rank_result = (
                    detect_entity_rank(
                        entity,
                        sentence
                    )
                )

                if rank_result["largest"]:
                    result["largest"] = True

                if rank_result["second_largest"]:
                    result["second_largest"] = True

                if rank_result["smallest"]:
                    result["smallest"] = True

                if rank_result["second_smallest"]:
                    result["second_smallest"] = True

            if (
                exact_title_match
                or entity_lower
                in normalized_sentence
            ):

                result[
                    "area_values"
                ].extend(
                    extract_area_values(
                        sentence
                    )
                )

                result[
                    "diameter_values"
                ].extend(
                    extract_diameter_values(
                        sentence
                    )
                )

                result[
                    "radius_values"
                ].extend(
                    extract_radius_values(
                        sentence
                    )
                )

                temperature_values = (
                    extract_temperature_values(
                        sentence
                    )
                )

                if temperature_values:

                    if (
                        has_preferred_temperature_context(
                            sentence
                        )
                    ):

                        result[
                            "preferred_temperature_values"
                        ].extend(
                            temperature_values
                        )

                    else:

                        result[
                            "fallback_temperature_values"
                        ].extend(
                            temperature_values
                        )

    return result


# ============================================================
# SIZE COMPARISON
# ============================================================

def compare_numeric_size(
    subject_info: dict,
    object_info: dict
) -> tuple[str, float, float] | None:

    subject_diameter = subject_info.get(
        "diameter_values",
        []
    )

    object_diameter = object_info.get(
        "diameter_values",
        []
    )

    if (
        subject_diameter
        and object_diameter
    ):

        return (
            "diameter",
            max(subject_diameter),
            max(object_diameter)
        )

    subject_radius = subject_info.get(
        "radius_values",
        []
    )

    object_radius = object_info.get(
        "radius_values",
        []
    )

    if (
        subject_radius
        and object_radius
    ):

        return (
            "radius",
            max(subject_radius),
            max(object_radius)
        )

    subject_area = subject_info.get(
        "area_values",
        []
    )

    object_area = object_info.get(
        "area_values",
        []
    )

    if (
        subject_area
        and object_area
    ):

        return (
            "area",
            max(subject_area),
            max(object_area)
        )

    return None


# ============================================================
# TEMPERATURE COMPARISON
# ============================================================

def get_best_temperature(
    entity_info: dict
) -> float | None:

    preferred = entity_info.get(
        "preferred_temperature_values",
        []
    )

    if preferred:

        return max(
            preferred
        )

    fallback = entity_info.get(
        "fallback_temperature_values",
        []
    )

    if fallback:

        return max(
            fallback
        )

    return None


def compare_temperature(
    subject_info: dict,
    object_info: dict
) -> tuple[float, float] | None:

    subject_temperature = (
        get_best_temperature(
            subject_info
        )
    )

    object_temperature = (
        get_best_temperature(
            object_info
        )
    )

    if (
        subject_temperature is None
        or object_temperature is None
    ):

        return None

    return (
        subject_temperature,
        object_temperature
    )


# ============================================================
# MAIN REASONER
# ============================================================

def reason_about_comparison(
    claim: str,
    evidence: list[dict]
) -> dict | None:

    comparison = detect_comparison_claim(
        claim
    )

    if not comparison:
        return None

    subject = comparison[
        "subject"
    ]

    relation = comparison[
        "relation"
    ]

    comparison_object = comparison[
        "object"
    ]

    subject_info = (
        find_entity_information(
            subject,
            evidence
        )
    )

    object_info = (
        find_entity_information(
            comparison_object,
            evidence
        )
    )

    # ========================================================
    # SIZE RANK REASONING
    # ========================================================

    if relation in {
        "larger",
        "bigger",
        "greater"
    }:

        if (
            subject_info["largest"]
            and object_info["second_largest"]
        ):

            return {
                "verdict": "SUPPORTED",
                "confidence": 0.95,
                "reason": (
                    f"Retrieved evidence identifies "
                    f"{subject} as the largest and "
                    f"{comparison_object} as the "
                    f"second largest."
                )
            }

        if (
            subject_info["largest"]
            and object_info["smallest"]
        ):

            return {
                "verdict": "SUPPORTED",
                "confidence": 0.95,
                "reason": (
                    f"Retrieved evidence identifies "
                    f"{subject} as the largest and "
                    f"{comparison_object} as the smallest."
                )
            }

        if (
            subject_info["smallest"]
            and object_info["largest"]
        ):

            return {
                "verdict": "REFUTED",
                "confidence": 0.95,
                "reason": (
                    f"Retrieved evidence identifies "
                    f"{subject} as the smallest and "
                    f"{comparison_object} as the largest."
                )
            }

    if relation == "smaller":

        if (
            subject_info["smallest"]
            and object_info["largest"]
        ):

            return {
                "verdict": "SUPPORTED",
                "confidence": 0.95,
                "reason": (
                    f"Retrieved evidence identifies "
                    f"{subject} as the smallest and "
                    f"{comparison_object} as the largest."
                )
            }

        if (
            subject_info["largest"]
            and object_info["smallest"]
        ):

            return {
                "verdict": "REFUTED",
                "confidence": 0.95,
                "reason": (
                    f"Retrieved evidence identifies "
                    f"{subject} as the largest and "
                    f"{comparison_object} as the smallest."
                )
            }

    # ========================================================
    # NUMERIC SIZE REASONING
    # ========================================================

    if relation in {
        "larger",
        "bigger",
        "greater",
        "smaller"
    }:

        numeric_result = (
            compare_numeric_size(
                subject_info,
                object_info
            )
        )

        if numeric_result is not None:

            (
                measurement_type,
                subject_value,
                object_value
            ) = numeric_result

            if relation in {
                "larger",
                "bigger",
                "greater"
            }:

                verdict = (
                    "SUPPORTED"
                    if subject_value
                    > object_value
                    else "REFUTED"
                )

            else:

                verdict = (
                    "SUPPORTED"
                    if subject_value
                    < object_value
                    else "REFUTED"
                )

            unit = (
                "km²"
                if measurement_type
                == "area"
                else "km"
            )

            return {
                "verdict": verdict,
                "confidence": 0.97,
                "reason": (
                    f"Retrieved evidence gives "
                    f"{subject} a {measurement_type} "
                    f"of approximately "
                    f"{subject_value:,.0f} {unit} and "
                    f"{comparison_object} a "
                    f"{measurement_type} of approximately "
                    f"{object_value:,.0f} {unit}."
                )
            }

    # ========================================================
    # TEMPERATURE REASONING
    # ========================================================

    if relation in {
        "hotter",
        "warmer",
        "colder",
        "cooler"
    }:

        temperature_result = (
            compare_temperature(
                subject_info,
                object_info
            )
        )

        if temperature_result is None:

            return None

        (
            subject_temperature,
            object_temperature
        ) = temperature_result

        if relation in {
            "hotter",
            "warmer"
        }:

            verdict = (
                "SUPPORTED"
                if subject_temperature
                > object_temperature
                else "REFUTED"
            )

        else:

            verdict = (
                "SUPPORTED"
                if subject_temperature
                < object_temperature
                else "REFUTED"
            )

        return {
            "verdict": verdict,
            "confidence": 0.97,
            "reason": (
                f"Retrieved comparable temperature evidence "
                f"gives {subject} approximately "
                f"{subject_temperature:.1f} °C and "
                f"{comparison_object} approximately "
                f"{object_temperature:.1f} °C."
            )
        }

    return None