import re

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


MODEL_NAME = "BAAI/bge-base-en-v1.5"

model = SentenceTransformer(
    MODEL_NAME
)


QUERY_INSTRUCTION = (
    "Represent this sentence for searching relevant passages: "
)


# ============================================================
# LIGHTWEIGHT PRE-FILTER SETTINGS
# ============================================================

MAX_BGE_CANDIDATES = 30


STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "of",
    "to",
    "in",
    "on",
    "at",
    "for",
    "from",
    "and",
    "or",
    "that",
    "this",
    "with",
    "by",
    "as",
    "than"
}


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(
    text: str
) -> list[str]:

    words = re.findall(
        r"\b[a-zA-Z0-9'-]+\b",
        text.lower()
    )

    return [
        word
        for word in words
        if (
            word not in STOPWORDS
            and len(word) > 1
        )
    ]


# ============================================================
# CHEAP LEXICAL SCORE
# ============================================================

def calculate_lexical_score(
    query: str,
    evidence_item: dict
) -> float:

    query_tokens = tokenize(
        query
    )

    text = evidence_item.get(
        "text",
        ""
    )

    title = evidence_item.get(
        "title",
        ""
    )

    text_tokens = set(
        tokenize(
            text
        )
    )

    title_tokens = set(
        tokenize(
            title
        )
    )

    if not query_tokens:
        return 0.0

    score = 0.0

    for token in query_tokens:

        if token in text_tokens:
            score += 1.0

        if token in title_tokens:
            score += 2.0

    normalized_query = (
        " ".join(
            query.lower().split()
        )
    )

    normalized_text = (
        " ".join(
            text.lower().split()
        )
    )

    if (
        normalized_query
        and normalized_query
        in normalized_text
    ):
        score += 5.0

    return score


# ============================================================
# PRE-FILTER
# ============================================================

def prefilter_evidence(
    query: str,
    evidence_items: list[dict],
    max_candidates: int = MAX_BGE_CANDIDATES
) -> list[dict]:

    if len(evidence_items) <= max_candidates:
        return evidence_items

    scored_items = []

    for item in evidence_items:

        lexical_score = (
            calculate_lexical_score(
                query,
                item
            )
        )

        scored_item = (
            item.copy()
        )

        scored_item[
            "lexical_score"
        ] = lexical_score

        scored_items.append(
            scored_item
        )

    scored_items.sort(
        key=lambda item: item[
            "lexical_score"
        ],
        reverse=True
    )

    return scored_items[
        :max_candidates
    ]


# ============================================================
# BGE SEMANTIC RANKER
# ============================================================

def rank_evidence(
    claim: str,
    evidence_items: list[dict],
    top_k: int = 5
) -> list[dict]:

    if not evidence_items:
        return []

    # --------------------------------------------------------
    # FAST PRE-FILTER
    # --------------------------------------------------------

    candidate_items = (
        prefilter_evidence(
            claim,
            evidence_items,
            max_candidates=(
                MAX_BGE_CANDIDATES
            )
        )
    )

    passages = [
        item["text"]
        for item in candidate_items
    ]

    query_text = (
        QUERY_INSTRUCTION
        + claim
    )

    # --------------------------------------------------------
    # BGE QUERY EMBEDDING
    # --------------------------------------------------------

    claim_embedding = (
        model.encode(
            query_text,
            convert_to_tensor=True,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False
        )
    )

    # --------------------------------------------------------
    # BGE PASSAGE EMBEDDINGS
    # --------------------------------------------------------

    passage_embeddings = (
        model.encode(
            passages,
            convert_to_tensor=True,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False
        )
    )

    # --------------------------------------------------------
    # COSINE SIMILARITY
    # --------------------------------------------------------

    similarity_scores = (
        cos_sim(
            claim_embedding,
            passage_embeddings
        )[0]
    )

    ranked_results = []

    for index, score in enumerate(
        similarity_scores
    ):

        evidence_item = (
            candidate_items[
                index
            ].copy()
        )

        evidence_item[
            "relevance_score"
        ] = float(
            score
        )

        ranked_results.append(
            evidence_item
        )

    ranked_results.sort(
        key=lambda item: item[
            "relevance_score"
        ],
        reverse=True
    )

    return ranked_results[
        :top_k
    ]