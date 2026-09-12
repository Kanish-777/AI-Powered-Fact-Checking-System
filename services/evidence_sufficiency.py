def has_sufficient_evidence(
    usable_evidence: list[dict],
    minimum_evidence: int = 2
) -> tuple[bool, str]:

    # -----------------------------------------
    # CASE 1:
    # MULTIPLE USABLE EVIDENCE ITEMS
    # -----------------------------------------

    if len(usable_evidence) >= minimum_evidence:

        return (
            True,
            "Multiple usable factual evidence items were available."
        )

    # -----------------------------------------
    # CASE 2:
    # NO USABLE EVIDENCE
    # -----------------------------------------

    if not usable_evidence:

        return (
            False,
            "No usable factual evidence was available."
        )

    # -----------------------------------------
    # CASE 3:
    # ONE EXCEPTIONALLY STRONG EVIDENCE ITEM
    # -----------------------------------------

    item = usable_evidence[0]

    verdict = item.get(
        "verdict",
        "INSUFFICIENT"
    )

    nli_confidence = item.get(
        "nli_confidence",
        0.0
    )

    relevance_score = item.get(
        "relevance_score",
        0.0
    )

    reranker_score = item.get(
        "reranker_score",
        0.0
    )

    # The passage must take an actual factual stance.
    if verdict not in {
        "SUPPORTED",
        "REFUTED"
    }:

        return (
            False,
            "The only available evidence did not take a strong factual stance."
        )

    # Very strong NLI agreement required.
    if nli_confidence < 0.95:

        return (
            False,
            "The only available evidence did not reach the required NLI confidence."
        )

    # It must still be semantically relevant.
    if relevance_score < 0.60:

        return (
            False,
            "The only available evidence was not sufficiently relevant."
        )

    # It must have already passed our Cross-Encoder gate.
    if reranker_score <= 1.0:

        return (
            False,
            "The only available evidence did not pass the relevance threshold."
        )

    return (
        True,
        "One exceptionally strong factual evidence item was available."
    )