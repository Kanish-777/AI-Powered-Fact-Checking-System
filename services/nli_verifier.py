import torch

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification
)


MODEL_NAME = (
    "MoritzLaurer/"
    "DeBERTa-v3-base-mnli-fever-anli"
)


# ============================================================
# LOAD MODEL ONCE
# ============================================================

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

model = (
    AutoModelForSequenceClassification
    .from_pretrained(
        MODEL_NAME
    )
)

model.eval()


# ============================================================
# LABEL ORDER
# ============================================================

LABELS = [
    "entailment",
    "neutral",
    "contradiction"
]


# ============================================================
# BUILD RESULT
# ============================================================

def build_verification_result(
    probabilities: list[float]
) -> dict:

    entailment_score = float(
        probabilities[0]
    )

    neutral_score = float(
        probabilities[1]
    )

    contradiction_score = float(
        probabilities[2]
    )

    scores = {
        "entailment": entailment_score,
        "neutral": neutral_score,
        "contradiction": contradiction_score
    }

    nli_label = max(
        scores,
        key=scores.get
    )

    nli_confidence = (
        scores[nli_label]
    )

    if nli_label == "entailment":

        verdict = "SUPPORTED"

    elif nli_label == "contradiction":

        verdict = "REFUTED"

    else:

        verdict = "INSUFFICIENT"

    return {
        "nli_label": nli_label,
        "verdict": verdict,
        "nli_confidence": nli_confidence,
        "entailment_score": entailment_score,
        "neutral_score": neutral_score,
        "contradiction_score": contradiction_score
    }


# ============================================================
# BATCH NLI
# ============================================================

def verify_claim_with_evidence_batch(
    claim: str,
    evidence_texts: list[str]
) -> list[dict]:

    if not evidence_texts:

        return []

    # Evidence = premise
    # Claim = hypothesis

    hypotheses = [
        claim
        for _ in evidence_texts
    ]

    encoded = tokenizer(
        evidence_texts,
        hypotheses,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt"
    )

    # ONE DeBERTa forward pass for all evidence passages.

    with torch.inference_mode():

        outputs = model(
            **encoded
        )

        probabilities = (
            torch.softmax(
                outputs.logits,
                dim=-1
            )
            .cpu()
            .tolist()
        )

    results = []

    for probability_row in probabilities:

        results.append(
            build_verification_result(
                probability_row
            )
        )

    return results


# ============================================================
# SINGLE-EVIDENCE COMPATIBILITY
# ============================================================

def verify_claim_with_evidence(
    claim: str,
    evidence_text: str
) -> dict:

    results = (
        verify_claim_with_evidence_batch(
            claim,
            [evidence_text]
        )
    )

    if not results:

        return {
            "nli_label": "neutral",
            "verdict": "INSUFFICIENT",
            "nli_confidence": 1.0,
            "entailment_score": 0.0,
            "neutral_score": 1.0,
            "contradiction_score": 0.0
        }

    return results[0]