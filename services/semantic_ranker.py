import re
from collections import OrderedDict

import torch

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


MODEL_NAME = "BAAI/bge-base-en-v1.5"


# ============================================================
# MODEL
# ============================================================

model = SentenceTransformer(
    MODEL_NAME
)


QUERY_INSTRUCTION = (
    "Represent this sentence for searching relevant passages: "
)


# ============================================================
# SETTINGS
# ============================================================

MAX_BGE_CANDIDATES = 30

# Cache embeddings of Wikipedia/scientific passages.
#
# The same page/chunk may appear under multiple generated
# queries. Without caching, BGE encodes that text repeatedly.
PASSAGE_CACHE_SIZE = 500

# Search queries can also repeat across claims.
QUERY_CACHE_SIZE = 100


# ============================================================
# SIMPLE LRU EMBEDDING CACHES
# ============================================================

_passage_embedding_cache = OrderedDict()

_query_embedding_cache = OrderedDict()


def _get_cached_embedding(
    cache: OrderedDict,
    key: str
):

    embedding = cache.get(
        key
    )

    if embedding is not None:

        cache.move_to_end(
            key
        )

    return embedding


def _store_cached_embedding(
    cache: OrderedDict,
    key: str,
    embedding: torch.Tensor,
    max_size: int
):

    cache[key] = (
        embedding
        .detach()
        .cpu()
    )

    cache.move_to_end(
        key
    )

    while len(cache) > max_size:

        cache.popitem(
            last=False
        )


# ============================================================
# STOPWORDS
# ============================================================

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
# QUERY EMBEDDING
# ============================================================

def get_query_embedding(
    claim: str
) -> torch.Tensor:

    query_text = (
        QUERY_INSTRUCTION
        + claim
    )

    cached = (
        _get_cached_embedding(
            _query_embedding_cache,
            query_text
        )
    )

    if cached is not None:

        return cached

    embedding = (
        model.encode(
            query_text,
            convert_to_tensor=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
    )

    embedding = (
        embedding
        .detach()
        .cpu()
    )

    _store_cached_embedding(
        _query_embedding_cache,
        query_text,
        embedding,
        QUERY_CACHE_SIZE
    )

    return embedding


# ============================================================
# PASSAGE EMBEDDINGS
# ============================================================

def get_passage_embeddings(
    passages: list[str]
) -> torch.Tensor:

    if not passages:

        return torch.empty(
            (0, 0)
        )

    # --------------------------------------------------------
    # Find passages that BGE has not already encoded.
    # --------------------------------------------------------

    missing_passages = []

    seen_missing = set()

    for passage in passages:

        cached = (
            _get_cached_embedding(
                _passage_embedding_cache,
                passage
            )
        )

        if (
            cached is None
            and passage not in seen_missing
        ):

            missing_passages.append(
                passage
            )

            seen_missing.add(
                passage
            )

    # --------------------------------------------------------
    # Encode ALL new passages together.
    #
    # This keeps the efficient BGE batch behaviour.
    # --------------------------------------------------------

    if missing_passages:

        new_embeddings = (
            model.encode(
                missing_passages,
                convert_to_tensor=True,
                normalize_embeddings=True,
                batch_size=32,
                show_progress_bar=False
            )
        )

        new_embeddings = (
            new_embeddings
            .detach()
            .cpu()
        )

        for passage, embedding in zip(
            missing_passages,
            new_embeddings
        ):

            _store_cached_embedding(
                _passage_embedding_cache,
                passage,
                embedding,
                PASSAGE_CACHE_SIZE
            )

    # --------------------------------------------------------
    # Reconstruct embeddings in original passage order.
    # --------------------------------------------------------

    ordered_embeddings = []

    for passage in passages:

        embedding = (
            _get_cached_embedding(
                _passage_embedding_cache,
                passage
            )
        )

        ordered_embeddings.append(
            embedding
        )

    return torch.stack(
        ordered_embeddings
    )


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
    # FAST LEXICAL PRE-FILTER
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
        item.get(
            "text",
            ""
        )
        for item in candidate_items
    ]

    # --------------------------------------------------------
    # BGE QUERY EMBEDDING
    # --------------------------------------------------------

    claim_embedding = (
        get_query_embedding(
            claim
        )
    )

    # --------------------------------------------------------
    # BGE PASSAGE EMBEDDINGS
    #
    # Previously every call encoded every passage again.
    #
    # Now already-seen chunks are reused.
    # --------------------------------------------------------

    passage_embeddings = (
        get_passage_embeddings(
            passages
        )
    )

    if passage_embeddings.numel() == 0:

        return []

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


# ============================================================
# OPTIONAL CACHE INFO
# ============================================================

def get_embedding_cache_info() -> dict:

    return {
        "cached_queries": len(
            _query_embedding_cache
        ),
        "cached_passages": len(
            _passage_embedding_cache
        )
    }