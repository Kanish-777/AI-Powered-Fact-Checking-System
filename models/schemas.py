from pydantic import BaseModel, Field


class ClaimRequest(BaseModel):

    claim: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Factual claim entered by the user"
    )


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

    evidence: list[dict]