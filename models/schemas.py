from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


# --------------------------------------------------
# Claim request
# --------------------------------------------------

class ClaimRequest(BaseModel):

    claim: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description=(
            "Factual claim entered by the user"
        )
    )


# --------------------------------------------------
# Individual evidence item
# --------------------------------------------------

class EvidenceItem(BaseModel):

    model_config = ConfigDict(
        extra="allow"
    )

    title: str | None = None

    source: str | None = None

    url: str | None = None

    text: str | None = None

    verdict: str | None = None

    relevance_score: float | None = None

    reranker_score: float | None = None

    nli_confidence: float | None = None

    entailment_score: float | None = None

    contradiction_score: float | None = None

    neutral_score: float | None = None

    exclude_from_aggregation: bool | None = None


# --------------------------------------------------
# Fact-check response
# --------------------------------------------------

class ClaimResponse(BaseModel):

    received_claim: str

    explanation: str

    status: str

    claim_domain: str

    final_verdict: str

    confidence: float

    support_score: float

    refute_score: float

    insufficient_score: float

    decision_margin: float

    decision_reason: str

    search_queries: list[str]

    evidence: list[EvidenceItem]


# --------------------------------------------------
# Individual history record
# --------------------------------------------------

class HistoryItem(BaseModel):

    id: int

    claim: str

    verdict: str

    confidence: float

    explanation: str | None = None

    claim_domain: str | None = None

    created_at: str | None = None


# --------------------------------------------------
# History response
# --------------------------------------------------

class HistoryResponse(BaseModel):

    history: list[HistoryItem]


# --------------------------------------------------
# Generic API message
# --------------------------------------------------

class MessageResponse(BaseModel):

    message: str