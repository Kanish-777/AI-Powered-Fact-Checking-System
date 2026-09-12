from services.source_credibility import get_source_credibility


MIN_DECISION_SCORE = 0.60
MIN_DECISION_MARGIN = 0.15

MIN_STANCE_SCORE = 0.75


def aggregate_verdict(
    verified_evidence: list[dict]
) -> dict:

    # -----------------------------------------
    # 1. REMOVE EXCLUDED EVIDENCE
    # -----------------------------------------

    usable_evidence = [
        item
        for item in verified_evidence
        if not item.get(
            "exclude_from_aggregation",
            False
        )
    ]

    if not usable_evidence:

        return {
            "final_verdict": "INSUFFICIENT",
            "confidence": 0.0,
            "support_score": 0.0,
            "refute_score": 0.0,
            "insufficient_score": 1.0,
            "decision_margin": 0.0,
            "decision_reason": (
                "No usable factual evidence was available."
            )
        }

    # -----------------------------------------
    # 2. FIND STANCE-BEARING EVIDENCE
    # -----------------------------------------

    stance_evidence = []

    for item in usable_evidence:

        strongest_factual_score = max(
            item["entailment_score"],
            item["contradiction_score"]
        )

        if (
            item["verdict"] in {
                "SUPPORTED",
                "REFUTED"
            }
            and strongest_factual_score
            >= MIN_STANCE_SCORE
        ):

            stance_evidence.append(
                item
            )

    # If direct stance evidence exists,
    # neutral passages should not drown it out.
    if stance_evidence:

        evidence_for_decision = (
            stance_evidence
        )

    else:

        evidence_for_decision = (
            usable_evidence
        )

    # -----------------------------------------
    # 3. AGGREGATE SCORES
    # -----------------------------------------

    support_score = 0.0
    refute_score = 0.0
    insufficient_score = 0.0

    for item in evidence_for_decision:

        relevance = item[
            "relevance_score"
        ]

        credibility = (
            get_source_credibility(
                item.get(
                    "source",
                    "Unknown"
                )
            )
        )

        weight = (
            relevance
            * credibility
        )

        support_score += (
            weight
            * item["entailment_score"]
        )

        refute_score += (
            weight
            * item["contradiction_score"]
        )

        insufficient_score += (
            weight
            * item["neutral_score"]
        )

    # -----------------------------------------
    # 4. NORMALIZE
    # -----------------------------------------

    total_score = (
        support_score
        + refute_score
        + insufficient_score
    )

    if total_score == 0:

        return {
            "final_verdict": "INSUFFICIENT",
            "confidence": 0.0,
            "support_score": 0.0,
            "refute_score": 0.0,
            "insufficient_score": 1.0,
            "decision_margin": 0.0,
            "decision_reason": (
                "Evidence scores could not "
                "produce a meaningful decision."
            )
        }

    support_score /= total_score
    refute_score /= total_score
    insufficient_score /= total_score

    # -----------------------------------------
    # 5. FIND STRONGEST FACTUAL VERDICT
    # -----------------------------------------

    factual_scores = {
        "SUPPORTED": support_score,
        "REFUTED": refute_score
    }

    strongest_verdict = max(
        factual_scores,
        key=factual_scores.get
    )

    strongest_score = (
        factual_scores[
            strongest_verdict
        ]
    )

    competing_score = (
        refute_score
        if strongest_verdict == "SUPPORTED"
        else support_score
    )

    decision_margin = (
        strongest_score
        - competing_score
    )

    # -----------------------------------------
    # 6. NEUTRAL DOMINATES
    # -----------------------------------------

    if (
        insufficient_score > support_score
        and insufficient_score > refute_score
    ):

        return {
            "final_verdict": "INSUFFICIENT",
            "confidence": insufficient_score,
            "support_score": support_score,
            "refute_score": refute_score,
            "insufficient_score": insufficient_score,
            "decision_margin": decision_margin,
            "decision_reason": (
                "Neutral or insufficient evidence "
                "received the strongest aggregate score."
            )
        }

    # -----------------------------------------
    # 7. MINIMUM SCORE CHECK
    # -----------------------------------------

    if strongest_score < MIN_DECISION_SCORE:

        return {
            "final_verdict": "INSUFFICIENT",
            "confidence": strongest_score,
            "support_score": support_score,
            "refute_score": refute_score,
            "insufficient_score": insufficient_score,
            "decision_margin": decision_margin,
            "decision_reason": (
                "The strongest factual position did not "
                "reach the minimum decision threshold."
            )
        }

    # -----------------------------------------
    # 8. CONFLICT CHECK
    # -----------------------------------------

    if decision_margin < MIN_DECISION_MARGIN:

        return {
            "final_verdict": "INSUFFICIENT",
            "confidence": strongest_score,
            "support_score": support_score,
            "refute_score": refute_score,
            "insufficient_score": insufficient_score,
            "decision_margin": decision_margin,
            "decision_reason": (
                "Supporting and refuting evidence were "
                "too close for a reliable verdict."
            )
        }

    # -----------------------------------------
    # 9. FINAL FACTUAL VERDICT
    # -----------------------------------------

    return {
        "final_verdict": strongest_verdict,
        "confidence": strongest_score,
        "support_score": support_score,
        "refute_score": refute_score,
        "insufficient_score": insufficient_score,
        "decision_margin": decision_margin,
        "decision_reason": (
            f"{strongest_verdict} passed both the "
            "minimum score and decision-margin thresholds."
        )
    }