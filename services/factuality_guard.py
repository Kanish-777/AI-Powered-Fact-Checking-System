import re


NON_FACTUAL_PATTERNS = [
    r"\bfanciful belief\b",
    r"\bfolklore\b",
    r"\bfiction\b",
    r"\bfictional\b",
    r"\bmyth\b",
    r"\bmisconception\b",
    r"\brumor\b",
    r"\brumour\b",
    r"\bhoax\b",
    r"\blegend\b",
    r"\burban legend\b",
    r"\bproverb\b",
    r"\bmetaphor\b",
    r"\bparody\b",
    r"\bsatire\b",
    r"\bsatirical\b",
    r"\bfalse claim\b",
    r"\bfalse belief\b",
    r"\bconspiracy theory\b",
    r"\bapril fools\b",
    r"\bspoof\b"
]


BELIEF_REPORTING_PATTERNS = [
    r"\bpeople believe\b",
    r"\bpeople believed\b",
    r"\bbelieve that\b",
    r"\bbelieved that\b",
    r"\bbelieves that\b",
    r"\bclaimed that\b",
    r"\bclaims that\b",
    r"\bthought that\b",
    r"\bwas thought to\b",
    r"\bwere thought to\b",
    r"\bwidely believed\b",
    r"\bcommonly believed\b",
    r"\bhistorically believed\b",
    r"\bpoll found\b",
    r"\bpolls found\b",
    r"\bsurvey found\b",
    r"\bsurveys found\b",
    r"\brespondents believed\b",
    r"\bpopulation believe\b",
    r"\badults believe\b",
    r"\baccording to a poll\b",
    r"\baccording to a survey\b"
]


EXPLICIT_REFUTATION_PATTERNS = [
    r"\bscientifically disproven\b",
    r"\bscientifically false\b",
    r"\bhas been disproven\b",
    r"\bhas been debunked\b",
    r"\bwas disproven\b",
    r"\bwas debunked\b",
    r"\bthoroughly debunked\b",
    r"\bdebunked many times\b",
    r"\bcannot be seen\b",
    r"\bcan not be seen\b",
    r"\bis not visible\b",
    r"\bnot visible\b",
    r"\bincorrect\b",
    r"\bnot true\b",
    r"\bfalse assertion\b"
]


def find_matching_patterns(
    text: str,
    patterns: list[str]
) -> list[str]:

    matches = []

    for pattern in patterns:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        ):
            matches.append(pattern)

    return matches


def apply_factuality_guard(
    evidence_text: str,
    verification: dict
) -> dict:

    guarded = verification.copy()

    non_factual_matches = find_matching_patterns(
        evidence_text,
        NON_FACTUAL_PATTERNS
    )

    belief_matches = find_matching_patterns(
        evidence_text,
        BELIEF_REPORTING_PATTERNS
    )

    refutation_matches = find_matching_patterns(
        evidence_text,
        EXPLICIT_REFUTATION_PATTERNS
    )

    has_non_factual_context = bool(
        non_factual_matches
    )

    has_belief_context = bool(
        belief_matches
    )

    has_explicit_refutation = bool(
        refutation_matches
    )

    guarded[
        "factuality_guard_triggered"
    ] = has_non_factual_context

    guarded[
        "belief_context_triggered"
    ] = has_belief_context

    guarded[
        "exclude_from_aggregation"
    ] = False

    # -----------------------------------------
    # EXPLICIT FACTUAL REFUTATION
    # -----------------------------------------

    if (
        verification["verdict"] == "REFUTED"
        and has_explicit_refutation
    ):

        guarded[
            "explicit_refutation_detected"
        ] = True

        return guarded

    guarded[
        "explicit_refutation_detected"
    ] = False

    # -----------------------------------------
    # NORMAL FACTUAL PASSAGE
    # -----------------------------------------

    if (
        not has_non_factual_context
        and not has_belief_context
    ):

        return guarded

    # -----------------------------------------
    # CONTEXTUAL / BELIEF PASSAGE
    # -----------------------------------------

    guarded[
        "exclude_from_aggregation"
    ] = True

    if has_non_factual_context:

        guarded[
            "factuality_context"
        ] = (
            "Evidence contains myth, fiction, folklore, satire, "
            "rumor, or other non-factual framing."
        )

    if has_belief_context:

        guarded[
            "belief_context"
        ] = (
            "Evidence reports that people or groups believe, "
            "claim, or previously believed the proposition, "
            "rather than establishing the proposition as fact."
        )

    # -----------------------------------------
    # PREVENT FALSE NLI SUPPORT
    # -----------------------------------------

    if verification["verdict"] == "SUPPORTED":

        guarded[
            "original_nli_label"
        ] = verification["nli_label"]

        guarded[
            "original_nli_confidence"
        ] = verification["nli_confidence"]

        original_entailment = verification[
            "entailment_score"
        ]

        original_neutral = verification[
            "neutral_score"
        ]

        guarded[
            "entailment_score"
        ] = 0.0

        guarded[
            "neutral_score"
        ] = min(
            1.0,
            original_neutral
            + original_entailment
        )

        guarded[
            "nli_label"
        ] = "neutral"

        guarded[
            "verdict"
        ] = "INSUFFICIENT"

        guarded[
            "nli_confidence"
        ] = guarded[
            "neutral_score"
        ]

    return guarded