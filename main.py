from fastapi import FastAPI

from models.schemas import ClaimRequest, ClaimResponse
from services.claim_service import process_claim


app = FastAPI(
    title="AI-Powered Fact Checking System",
    description="Backend API for evidence-based fact verification",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "AI Fact Checking System is running"
    }


@app.post("/check-claim", response_model=ClaimResponse)
def check_claim(data: ClaimRequest):
    return process_claim(data.claim)