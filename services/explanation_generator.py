import re


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:

    return re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()


# ============================================================
# EXTRACT MAIN CLAIM SUBJECT
# ============================================================

def extract_claim_subject(
    claim: str
) -> str:

    cleaned = claim.strip()

    # --------------------------------------------------------
    # Handles common factual structures:
    #
    # The Sun is a planet
    # Venus is hotter than Earth
    # Water is made of ...
    # Humans have ...
    # Penguins are native to ...
    # --------------------------------------------------------

    patterns = [
        r"^(?:the\s+)?(.+?)\s+is\s+",
        r"^(?:the\s+)?(.+?)\s+are\s+",
        r"^(?:the\s+)?(.+?)\s+has\s+",
        r"^(?:the\s+)?(.+?)\s+have\s+",
        r"^(?:the\s+)?(.+?)\s+was\s+",
        r"^(?:the\s+)?(.+?)\s+were\s+"
    ]

    for pattern in patterns:

        match = re.match(
            pattern,
            cleaned,
            flags=re.IGNORECASE
        )

        if match:

            return (
                match.group(1)
                .strip()
            )

    return ""


# ============================================================
# TITLE MATCHING
# ============================================================

def title_matches_subject(
    subject: str,
    title: str
) -> bool:

    if not subject or not title:
        return False

    subject_normalized = normalize_text(
        subject
    )

    title_normalized = normalize_text(
        title
    )

    # Exact title:
    #
    # Sun
    #
    # or parenthetical title:
    #
    # Mercury (planet)
    #

    pattern = (
        rf"^{re.escape(subject_normalized)}"
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
# EVIDENCE SCORE
# ============================================================

def calculate_explanation_score(
    claim: str,
    evidence_item: dict
) -> float:

    subject = (
        extract_claim_subject(
            claim
        )
    )

    title = evidence_item.get(
        "title",
        ""
    )

    text = evidence_item.get(
        "text",
        ""
    )

    reranker_score = float(
        evidence_item.get(
            "reranker_score",
            0.0
        )
    )

    relevance_score = float(
        evidence_item.get(
            "relevance_score",
            0.0
        )
    )

    nli_confidence = float(
        evidence_item.get(
            "nli_confidence",
            0.0
        )
    )

    score = 0.0

    # ========================================================
    # 1. NLI CONFIDENCE
    # ========================================================

    score += (
        nli_confidence
        * 4.0
    )

    # ========================================================
    # 2. CROSS-ENCODER SCORE
    # ========================================================

    # Cap it so one unusually large Cross-Encoder score
    # cannot completely dominate explanation selection.

    capped_reranker = min(
        max(
            reranker_score,
            0.0
        ),
        10.0
    )

    score += (
        capped_reranker
        * 0.35
    )

    # ========================================================
    # 3. BGE RELEVANCE
    # ========================================================

    score += (
        relevance_score
        * 2.0
    )

    # ========================================================
    # 4. DIRECT ENTITY TITLE BONUS
    # ========================================================
    #
    # Example:
    #
    # Claim:
    # "The Sun is a planet"
    #
    # Wikipedia page:
    # "Sun"
    #
    # This should generally be preferred over:
    # "Mercury (planet)"
    #
    # even if Mercury happens to contradict the claim.
    # ========================================================

    if title_matches_subject(
        subject,
        title
    ):

        score += 5.0

    # ========================================================
    # 5. SUBJECT PRESENT IN EVIDENCE TEXT
    # ========================================================

    if subject:

        subject_normalized = (
            normalize_text(
                subject
            )
        )

        text_normalized = (
            normalize_text(
                text
            )
        )

        if subject_normalized in text_normalized:

            score += 1.0

    return score


# ============================================================
# SELECT BEST EVIDENCE
# ============================================================

def select_best_explanation_evidence(
    claim: str,
    verdict: str,
    evidence_items: list[dict]
) -> dict | None:

    if not evidence_items:
        return None

    # --------------------------------------------------------
    # Ignore evidence explicitly excluded by guards.
    # --------------------------------------------------------

    usable_evidence = [
        item
        for item in evidence_items
        if not item.get(
            "exclude_from_aggregation",
            False
        )
    ]

    if not usable_evidence:
        return None

    # --------------------------------------------------------
    # Match evidence stance with final verdict.
    # --------------------------------------------------------

    if verdict == "SUPPORTED":

        matching_evidence = [
            item
            for item in usable_evidence
            if item.get(
                "verdict"
            ) == "SUPPORTED"
        ]

    elif verdict == "REFUTED":

        matching_evidence = [
            item
            for item in usable_evidence
            if item.get(
                "verdict"
            ) == "REFUTED"
        ]

    else:

        matching_evidence = [
            item
            for item in usable_evidence
            if item.get(
                "verdict"
            ) == "INSUFFICIENT"
        ]

    # --------------------------------------------------------
    # If no stance-matching evidence exists, fall back to
    # all usable evidence.
    # --------------------------------------------------------

    candidates = (
        matching_evidence
        if matching_evidence
        else usable_evidence
    )

    scored_candidates = []

    for item in candidates:

        explanation_score = (
            calculate_explanation_score(
                claim,
                item
            )
        )

        scored_item = (
            item.copy()
        )

        scored_item[
            "explanation_score"
        ] = explanation_score

        scored_candidates.append(
            scored_item
        )

    scored_candidates.sort(
        key=lambda item: item[
            "explanation_score"
        ],
        reverse=True
    )

    return scored_candidates[0]


# ============================================================
# MAIN EXPLANATION GENERATOR
# ============================================================

def generate_explanation(
    claim: str,
    verdict: str,
    evidence_items: list[dict]
) -> str:

    # ========================================================
    # INSUFFICIENT
    # ========================================================

    if verdict == "INSUFFICIENT":

        return (
            f'The available evidence is not strong or '
            f'consistent enough to confidently support '
            f'or refute the claim "{claim}".'
        )

    # ========================================================
    # BEST EVIDENCE
    # ========================================================

    best_evidence = (
        select_best_explanation_evidence(
            claim,
            verdict,
            evidence_items
        )
    )

    if best_evidence is None:

        if verdict == "SUPPORTED":

            return (
                f'The claim "{claim}" is supported '
                f'by the retrieved evidence.'
            )

        if verdict == "REFUTED":

            return (
                f'The claim "{claim}" is refuted '
                f'by the retrieved evidence.'
            )

    title = best_evidence.get(
        "title",
        "retrieved source"
    )

    # ========================================================
    # SUPPORTED
    # ========================================================

    if verdict == "SUPPORTED":

        return (
            f'The claim "{claim}" is supported by the '
            f'retrieved evidence. The strongest supporting '
            f'evidence comes from "{title}", which provides '
            f'factual information directly consistent with '
            f'the claim.'
        )

    # ========================================================
    # REFUTED
    # ========================================================

    if verdict == "REFUTED":

        return (
            f'The claim "{claim}" is refuted by the '
            f'retrieved evidence. The strongest contradictory '
            f'evidence comes from "{title}", which provides '
            f'factual information directly inconsistent with '
            f'the claim.'
        )

    # ========================================================
    # FALLBACK
    # ========================================================

    return (
        f'The claim "{claim}" was evaluated using '
        f'the retrieved evidence.'
    )