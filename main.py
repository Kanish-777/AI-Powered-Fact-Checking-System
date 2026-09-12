from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from models.schemas import (
    ClaimRequest,
    ClaimResponse,
    HistoryResponse,
    MessageResponse
)

from services.claim_service import (
    process_claim
)

from services.history_database import (
    initialize_database,
    save_claim_result,
    get_claim_history,
    clear_claim_history
)


app = FastAPI(
    title="AI-Powered Fact Checking System",
    description=(
        "Evidence-based AI fact verification "
        "using semantic retrieval, reranking "
        "and Natural Language Inference."
    ),
    version="1.0.0"
)


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
)

FRONTEND_FILE = (
    BASE_DIR
    / "frontend"
    / "index.html"
)


# --------------------------------------------------
# Database initialization
# --------------------------------------------------

try:
    initialize_database()

except Exception as error:

    print(
        "[DATABASE ERROR] "
        f"Initialization failed: {error}"
    )


# --------------------------------------------------
# Frontend
# --------------------------------------------------

@app.get(
    "/",
    include_in_schema=False
)
def home():

    if not FRONTEND_FILE.exists():

        raise HTTPException(
            status_code=500,
            detail=(
                "Frontend file could not be found."
            )
        )

    return FileResponse(
        FRONTEND_FILE
    )


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get(
    "/health",
    tags=["System"]
)
def health():

    return {
        "status": "online",
        "message":
            "AI Fact Checking System is running"
    }


# --------------------------------------------------
# Fact-check endpoint
# --------------------------------------------------

@app.post(
    "/check-claim",
    response_model=ClaimResponse,
    tags=["Fact Checking"]
)
def check_claim(
    data: ClaimRequest
):

    try:

        result = process_claim(
            data.claim
        )

    except Exception as error:

        print(
            "[FACT CHECK ERROR] "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The claim could not be verified "
                "because the verification pipeline "
                "encountered an internal error."
            )
        )


    try:

        save_claim_result(
            claim=
                result["received_claim"],

            verdict=
                result["final_verdict"],

            confidence=
                result["confidence"],

            explanation=
                result["explanation"],

            claim_domain=
                result["claim_domain"]
        )

    except Exception as error:

        # Database failure should not destroy
        # an otherwise successful fact-check.
        print(
            "[DATABASE ERROR] "
            f"Could not save claim history: {error}"
        )


    return result


# --------------------------------------------------
# Claim history
# --------------------------------------------------

@app.get(
    "/history",
    response_model=HistoryResponse,
    tags=["History"]
)
def history():

    try:

        records = get_claim_history(
            limit=50
        )

    except Exception as error:

        print(
            "[DATABASE ERROR] "
            f"Could not load history: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Claim history could not be loaded."
            )
        )


    return {
        "history":
            records
    }


# --------------------------------------------------
# Clear claim history
# --------------------------------------------------

@app.delete(
    "/history",
    response_model=MessageResponse,
    tags=["History"]
)
def delete_history():

    try:

        clear_claim_history()

    except Exception as error:

        print(
            "[DATABASE ERROR] "
            f"Could not clear history: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Claim history could not be cleared."
            )
        )


    return {
        "message":
            "Claim history cleared successfully."
    }