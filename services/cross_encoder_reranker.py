from sentence_transformers import CrossEncoder


RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"

reranker = CrossEncoder(
    RERANKER_MODEL_NAME
)


def rerank_evidence(
    claim: str,
    evidence_items: list[dict],
    top_k: int = 10
) -> list[dict]:

    if not evidence_items:
        return []

    pairs = [
        [claim, item["text"]]
        for item in evidence_items
    ]

    scores = reranker.predict(
        pairs
    )

    reranked_results = []

    for item, score in zip(
        evidence_items,
        scores
    ):

        reranked_item = item.copy()

        reranked_item["reranker_score"] = float(
            score
        )

        reranked_results.append(
            reranked_item
        )

    reranked_results.sort(
        key=lambda item: item["reranker_score"],
        reverse=True
    )

    return reranked_results[:top_k]