import re


STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "of",
    "to",
    "in",
    "on",
    "for",
    "and",
    "or",
    "that"
}


COMPARISON_ATTRIBUTES = {
    "larger": "size",
    "smaller": "size",
    "bigger": "size",
    "greater": "size",
    "higher": "height",
    "lower": "height",
    "longer": "length",
    "shorter": "length",
    "older": "age",
    "younger": "age",
    "faster": "speed",
    "slower": "speed",
    "heavier": "weight",
    "lighter": "weight",
    "hotter": "temperature",
    "colder": "temperature",
    "warmer": "temperature",
    "cooler": "temperature"
}


# ============================================================
# RETRIEVAL-ONLY TYPO NORMALIZATION
# ============================================================

def normalize_retrieval_claim(
    claim: str
) -> str:

    normalized = " ".join(
        claim.strip().split()
    )

    # --------------------------------------------------------
    # Conservative typo corrections for common function words.
    #
    # IMPORTANT:
    # This only affects search/query generation.
    # The original claim displayed to the user is unchanged.
    # --------------------------------------------------------

    corrections = {
        "ia": "is",
        "si": "is",
        "iz": "is",

        "teh": "the",
        "hte": "the",

        "rae": "are",
        "aer": "are",

        "wsa": "was"
    }

    words = normalized.split()

    corrected_words = []

    for word in words:

        match = re.match(
            r"^([A-Za-z]+)([^A-Za-z]*)$",
            word
        )

        if not match:

            corrected_words.append(
                word
            )

            continue

        base_word = match.group(1)

        punctuation = match.group(2)

        corrected_word = corrections.get(
            base_word.lower(),
            base_word
        )

        # Preserve capitalization style.
        if base_word.isupper():

            corrected_word = (
                corrected_word.upper()
            )

        elif base_word[0].isupper():

            corrected_word = (
                corrected_word.capitalize()
            )

        corrected_words.append(
            corrected_word + punctuation
        )

    return " ".join(
        corrected_words
    )


# ============================================================
# SINGULARIZATION
# ============================================================

def singularize_word(
    word: str
) -> str:

    lower_word = word.lower()

    if lower_word.endswith("ies"):
        return word[:-3] + "y"

    if lower_word.endswith("ses"):
        return word[:-2]

    if (
        lower_word.endswith("s")
        and not lower_word.endswith("ss")
    ):
        return word[:-1]

    return word


# ============================================================
# SUBJECT NORMALIZATION
# ============================================================

def normalize_subject(
    subject: str
) -> str:

    normalized = subject.strip()

    replacements = {
        "humans": "human",
        "people": "human"
    }

    return replacements.get(
        normalized.lower(),
        normalized
    )


# ============================================================
# SEARCH QUERY GENERATION
# ============================================================

def generate_search_queries(
    claim: str,
    max_queries: int = 4
) -> list[str]:

    # --------------------------------------------------------
    # Retrieval-only normalization.
    #
    # Example:
    #
    # User:
    # THE SUN IA A PLANET
    #
    # Internal retrieval:
    # THE SUN IS A PLANET
    #
    # Original claim itself is NOT modified.
    # --------------------------------------------------------

    cleaned_claim = normalize_retrieval_claim(
        claim
    )

    queries = [
        cleaned_claim
    ]

    lower_claim = cleaned_claim.lower()

    # ========================================================
    # 1. COUNT CLAIMS
    # ========================================================

    count_match = re.match(
        r"^(?:the\s+)?(.+?)\s+"
        r"(?:have|has)\s+"
        r"(one|two|three|four|five|six|seven|eight|nine|ten|"
        r"hundred|thousand|\d+)\s+"
        r"(.+?)[.!?]?$",
        cleaned_claim,
        flags=re.IGNORECASE
    )

    if count_match:

        subject = normalize_subject(
            count_match.group(1)
        )

        object_phrase = (
            count_match
            .group(3)
            .strip()
        )

        object_words = (
            object_phrase.split()
        )

        singular_object_words = (
            object_words.copy()
        )

        if singular_object_words:

            singular_object_words[-1] = (
                singularize_word(
                    singular_object_words[-1]
                )
            )

        singular_object = " ".join(
            singular_object_words
        )

        subject_lower = (
            subject.lower()
        )

        if (
            "human" in subject_lower
            or "body" in subject_lower
        ):

            queries.append(
                f"number of {object_phrase} "
                f"in human body"
            )

            queries.append(
                f"human {singular_object} anatomy"
            )

        else:

            queries.append(
                f"number of {object_phrase} "
                f"in {subject}"
            )

            queries.append(
                f"{subject} {singular_object}"
            )

    # ========================================================
    # 2. COMPARISON CLAIMS
    # ========================================================

    comparison_match = re.match(
        r"^(?:the\s+)?(.+?)\s+is\s+"
        r"(larger|smaller|bigger|greater|higher|lower|"
        r"longer|shorter|older|younger|faster|slower|"
        r"heavier|lighter|hotter|colder|warmer|cooler)\s+than\s+"
        r"(?:the\s+)?(.+?)[.!?]?$",
        cleaned_claim,
        flags=re.IGNORECASE
    )

    if comparison_match:

        subject = (
            comparison_match
            .group(1)
            .strip()
        )

        relation = (
            comparison_match
            .group(2)
            .lower()
        )

        comparison_object = (
            comparison_match
            .group(3)
            .strip()
        )

        attribute = (
            COMPARISON_ATTRIBUTES.get(
                relation,
                "comparison"
            )
        )

        # ----------------------------------------------------
        # TEMPERATURE COMPARISONS
        # ----------------------------------------------------
        #
        # Example:
        # Venus is hotter than Earth
        #
        # Search actual/surface temperatures rather than vague
        # "temperature", which may retrieve black-body or
        # equilibrium temperature.
        # ----------------------------------------------------

        if relation in {
            "hotter",
            "warmer",
            "colder",
            "cooler"
        }:

            queries.append(
                f"{subject} {comparison_object} "
                f"surface temperature comparison"
            )

            queries.append(
                f"{subject} surface temperature"
            )

            queries.append(
                f"{comparison_object} surface temperature"
            )

        # ----------------------------------------------------
        # OTHER COMPARISONS
        # ----------------------------------------------------

        else:

            queries.append(
                f"{subject} {comparison_object} "
                f"{attribute} comparison"
            )

            queries.append(
                f"{subject} {attribute}"
            )

            queries.append(
                f"{comparison_object} {attribute}"
            )

    # ========================================================
    # 3. LOCATION CLAIMS
    # ========================================================

    location_match = re.match(
        r"^(?:the\s+)?(.+?)\s+"
        r"(?:is|are)\s+located\s+"
        r"(?:inside|in|within|at|on)\s+"
        r"(?:the\s+)?(.+?)[.!?]?$",
        cleaned_claim,
        flags=re.IGNORECASE
    )

    if location_match:

        subject = (
            location_match
            .group(1)
            .strip()
        )

        queries.append(
            f"{subject} location"
        )

        queries.append(
            f"{subject} anatomy"
        )

    # ========================================================
    # 4. NATIVE RANGE CLAIMS
    # ========================================================

    native_match = re.match(
        r"^(?:the\s+)?(.+?)\s+"
        r"(?:is|are)\s+native\s+to\s+"
        r"(?:the\s+)?(.+?)[.!?]?$",
        cleaned_claim,
        flags=re.IGNORECASE
    )

    if native_match:

        subject = (
            native_match
            .group(1)
            .strip()
        )

        queries.append(
            f"{subject} native range"
        )

        queries.append(
            f"{subject} distribution"
        )

    # ========================================================
    # 5. COMPOSITION CLAIMS
    # ========================================================

    made_of_match = re.search(
        r"\b(?:is|are)\s+made\s+(?:only\s+)?of\b",
        cleaned_claim,
        flags=re.IGNORECASE
    )

    if made_of_match:

        parts = re.split(
            r"\b(?:is|are)\s+made\s+(?:only\s+)?of\b",
            cleaned_claim,
            flags=re.IGNORECASE
        )

        if parts:

            subject = (
                parts[0]
                .strip()
            )

            subject = re.sub(
                r"^(the|a|an)\s+",
                "",
                subject,
                flags=re.IGNORECASE
            )

            queries.append(
                f"{subject} composition"
            )

            queries.append(
                f"{subject} chemical composition"
            )

    # ========================================================
    # 6. CLASSIFICATION CLAIMS
    # ========================================================

    classification_match = re.match(
        r"^(?:the\s+)?(.+?)\s+is\s+"
        r"(?:a|an)\s+(.+?)[.!?]?$",
        cleaned_claim,
        flags=re.IGNORECASE
    )

    if classification_match:

        subject = (
            classification_match
            .group(1)
            .strip()
        )

        category = (
            classification_match
            .group(2)
            .strip()
        )

        if (
            not comparison_match
            and not location_match
        ):

            queries.append(
                f"{subject} classification"
            )

            queries.append(
                f"{subject} type"
            )

            queries.append(
                f"{subject} {category}"
            )

    # ========================================================
    # 7. CAUSAL / RISK CLAIMS
    # ========================================================

    if (
        " causes " in lower_claim
        or " cause " in lower_claim
        or " increases the risk of " in lower_claim
        or " increase the risk of " in lower_claim
    ):

        keyword_query = (
            create_keyword_query(
                cleaned_claim
            )
        )

        queries.append(
            f"{keyword_query} relationship"
        )

    # ========================================================
    # 8. GENERAL KEYWORD QUERY
    # ========================================================

    keyword_query = (
        create_keyword_query(
            cleaned_claim
        )
    )

    if keyword_query:

        queries.append(
            keyword_query
        )

    # ========================================================
    # 9. REMOVE DUPLICATES
    # ========================================================

    unique_queries = []

    seen = set()

    for query in queries:

        normalized = (
            query
            .lower()
            .strip()
        )

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        unique_queries.append(
            query.strip()
        )

    return unique_queries[
        :max_queries
    ]


# ============================================================
# GENERAL KEYWORD QUERY
# ============================================================

def create_keyword_query(
    claim: str
) -> str:

    words = re.findall(
        r"\b[A-Za-z0-9'-]+\b",
        claim
    )

    important_words = [
        word
        for word in words
        if word.lower()
        not in STOPWORDS
    ]

    return " ".join(
        important_words
    )