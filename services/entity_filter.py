import re


def normalize_text(text: str) -> str:

    return re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()


def extract_query_entities(
    claim: str
) -> list[str]:

    cleaned = claim.strip()

    entities = []

    # --------------------------------------------------------
    # COMPARISON CLAIMS
    # Example:
    # Jupiter is smaller than Mercury
    # --------------------------------------------------------

    comparison_match = re.match(
        r"^(?:the\s+)?(.+?)\s+is\s+"
        r"(?:larger|smaller|bigger|greater|higher|lower|"
        r"longer|shorter|older|younger|faster|slower|"
        r"heavier|lighter)\s+than\s+"
        r"(?:the\s+)?(.+?)[.!?]?$",
        cleaned,
        flags=re.IGNORECASE
    )

    if comparison_match:

        entities.append(
            comparison_match.group(1).strip()
        )

        entities.append(
            comparison_match.group(2).strip()
        )

        return entities

    # --------------------------------------------------------
    # COUNT CLAIMS
    # Example:
    # Humans have three hearts
    # --------------------------------------------------------

    count_match = re.match(
        r"^(?:the\s+)?(.+?)\s+"
        r"(?:have|has)\s+"
        r"(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+"
        r"(.+?)[.!?]?$",
        cleaned,
        flags=re.IGNORECASE
    )

    if count_match:

        entities.append(
            count_match.group(1).strip()
        )

        return entities

    return entities


def title_exact_or_parenthetical_match(
    entity: str,
    title: str
) -> bool:

    entity_norm = normalize_text(
        entity
    )

    title_norm = normalize_text(
        title
    )

    pattern = (
        rf"^{re.escape(entity_norm)}"
        rf"(?:\s*\([^)]*\))?$"
    )

    return bool(
        re.fullmatch(
            pattern,
            title_norm,
            flags=re.IGNORECASE
        )
    )


def title_contains_entity_phrase(
    entity: str,
    title: str
) -> bool:

    entity_norm = normalize_text(
        entity
    )

    title_norm = normalize_text(
        title
    )

    return (
        entity_norm in title_norm
    )


def is_relevant_entity_page(
    claim: str,
    evidence_item: dict
) -> bool:

    title = evidence_item.get(
        "title",
        ""
    )

    search_query = evidence_item.get(
        "search_query",
        ""
    )

    entities = extract_query_entities(
        claim
    )

    # --------------------------------------------------------
    # If we cannot confidently extract entities,
    # do not filter the page.
    # --------------------------------------------------------

    if not entities:
        return True

    title_norm = normalize_text(
        title
    )

    search_query_norm = normalize_text(
        search_query
    )

    # --------------------------------------------------------
    # Strong match:
    # Mercury
    # Mercury (planet)
    # Jupiter
    # --------------------------------------------------------

    for entity in entities:

        if title_exact_or_parenthetical_match(
            entity,
            title
        ):
            return True

    # --------------------------------------------------------
    # Joint / context pages may also be useful:
    #
    # Planet
    # Solar System
    # Human body
    #
    # We retain them if the retrieved text or query was built
    # from multiple claim entities.
    # --------------------------------------------------------

    matched_query_entities = 0

    for entity in entities:

        if normalize_text(entity) in search_query_norm:
            matched_query_entities += 1

    if matched_query_entities >= 2:
        return True

    # --------------------------------------------------------
    # Reject ambiguous derivative pages.
    #
    # Example:
    #
    # Mercury Monterey
    # Mercury Marquis
    #
    # where "Mercury" is only a prefix of an unrelated title.
    # --------------------------------------------------------

    for entity in entities:

        entity_norm = normalize_text(
            entity
        )

        if (
            entity_norm in title_norm
            and not title_exact_or_parenthetical_match(
                entity,
                title
            )
        ):
            return False

    return True


def filter_entity_mismatches(
    claim: str,
    evidence_items: list[dict]
) -> list[dict]:

    filtered = []

    for item in evidence_items:

        if is_relevant_entity_page(
            claim,
            item
        ):
            filtered.append(
                item
            )

    return filtered