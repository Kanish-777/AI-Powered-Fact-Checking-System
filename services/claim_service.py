import time

from services.evidence_retriever import (
    search_wikipedia,
    get_wikipedia_pages_text
)

from services.text_processor import split_into_chunks

from services.semantic_ranker import (
    rank_evidence
)

from services.cross_encoder_reranker import (
    rerank_evidence
)

from services.nli_verifier import (
    verify_claim_with_evidence_batch
)

from services.factuality_guard import (
    apply_factuality_guard
)

from services.verdict_aggregator import (
    aggregate_verdict
)

from services.scientific_retriever import (
    search_scientific_evidence
)

from services.evidence_diversity import (
    select_diverse_evidence
)

from services.query_generator import (
    generate_search_queries
)

from services.explanation_generator import (
    generate_explanation
)

from services.evidence_sufficiency import (
    has_sufficient_evidence
)

from services.comparison_reasoner import (
    reason_about_comparison
)

from services.entity_filter import (
    filter_entity_mismatches
)

from services.domain_router import (
    detect_claim_domain,
    should_use_scientific_source
)


RERANKER_THRESHOLD = 1.0
MIN_STRONG_EVIDENCE = 2


# ============================================================
# TIMING HELPER
# ============================================================

def print_timing(
    label: str,
    start_time: float
):

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print(
        f"[TIMING] {label}: "
        f"{elapsed:.2f} seconds"
    )

    return elapsed


# ============================================================
# MAIN CLAIM PROCESSOR
# ============================================================

def process_claim(
    claim: str
) -> dict:

    total_start = (
        time.perf_counter()
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "FACT CHECK TIMING PROFILE"
    )

    print(
        "=" * 70
    )

    print(
        f"Claim: {claim}"
    )

    print(
        "-" * 70
    )

    cleaned_claim = (
        claim.strip()
    )

    # ========================================================
    # 1. DOMAIN DETECTION
    # ========================================================

    stage_start = (
        time.perf_counter()
    )

    claim_domain = (
        detect_claim_domain(
            cleaned_claim
        )
    )

    print_timing(
        "Domain detection",
        stage_start
    )

    global_chunk_id = 1

    wikipedia_shortlist = []

    scientific_evidence = []

    # ========================================================
    # 2. QUERY GENERATION
    # ========================================================

    stage_start = (
        time.perf_counter()
    )

    search_queries = (
        generate_search_queries(
            cleaned_claim,
            max_queries=4
        )
    )

    print_timing(
        "Query generation",
        stage_start
    )

    # ========================================================
    # 3. WIKIPEDIA PIPELINE
    # ========================================================

    wikipedia_total_start = (
        time.perf_counter()
    )

    wikipedia_search_time = 0.0

    wikipedia_page_time = 0.0

    chunking_time = 0.0

    bge_time = 0.0

    cross_encoder_time = 0.0

    query_search_results = {}

    all_page_ids = []

    # ========================================================
    # 4. WIKIPEDIA SEARCH
    # ========================================================

    for query in search_queries:

        print(
            f"\n[TIMING] Searching query: "
            f"{query}"
        )

        stage_start = (
            time.perf_counter()
        )

        search_results = (
            search_wikipedia(
                query,
                limit=5
            )
        )

        wikipedia_search_time += (
            time.perf_counter()
            - stage_start
        )

        # Keep three best pages PER query.
        #
        # We do NOT remove the same page when it appears
        # under another useful query.

        selected_results = (
            search_results[:3]
        )

        query_search_results[
            query
        ] = selected_results

        for search_result in selected_results:

            all_page_ids.append(
                search_result[
                    "page_id"
                ]
            )

    # ========================================================
    # 5. FULL WIKIPEDIA PAGE RETRIEVAL
    # ========================================================

    stage_start = (
        time.perf_counter()
    )

    wikipedia_pages = (
        get_wikipedia_pages_text(
            all_page_ids
        )
    )

    wikipedia_page_time = (
        time.perf_counter()
        - stage_start
    )

    # ========================================================
    # 6. PROCESS EACH GENERATED QUERY
    # ========================================================

    for query in search_queries:

        print(
            f"\n[TIMING] Processing query: "
            f"{query}"
        )

        query_evidence = []

        selected_results = (
            query_search_results.get(
                query,
                []
            )
        )

        # ----------------------------------------------------
        # BUILD CHUNKS
        # ----------------------------------------------------

        for search_result in selected_results:

            page_id = (
                search_result[
                    "page_id"
                ]
            )

            article_text = (
                wikipedia_pages.get(
                    page_id,
                    ""
                )
            )

            if not article_text:

                continue

            stage_start = (
                time.perf_counter()
            )

            chunks = (
                split_into_chunks(
                    article_text
                )
            )

            chunking_time += (
                time.perf_counter()
                - stage_start
            )

            for chunk in chunks:

                query_evidence.append({
                    "chunk_id": (
                        global_chunk_id
                    ),
                    "title": (
                        search_result[
                            "title"
                        ]
                    ),
                    "page_id": (
                        page_id
                    ),
                    "source": (
                        search_result[
                            "source"
                        ]
                    ),
                    "url": (
                        search_result[
                            "url"
                        ]
                    ),
                    "search_query": (
                        query
                    ),
                    "text": (
                        chunk
                    )
                })

                global_chunk_id += 1

        # ====================================================
        # 7. BGE SEMANTIC RANKING
        # ====================================================

        stage_start = (
            time.perf_counter()
        )

        query_ranked = (
            rank_evidence(
                query,
                query_evidence,
                top_k=6
            )
        )

        bge_time += (
            time.perf_counter()
            - stage_start
        )

        # ====================================================
        # 8. CROSS-ENCODER RERANKING
        # ====================================================

        stage_start = (
            time.perf_counter()
        )

        query_reranked = (
            rerank_evidence(
                query,
                query_ranked,
                top_k=len(
                    query_ranked
                )
            )
        )

        cross_encoder_time += (
            time.perf_counter()
            - stage_start
        )

        # ====================================================
        # 9. RELEVANCE THRESHOLD
        # ====================================================

        query_relevant = [
            item
            for item
            in query_reranked
            if item[
                "reranker_score"
            ] > RERANKER_THRESHOLD
        ]

        wikipedia_shortlist.extend(
            query_relevant[:2]
        )

    wikipedia_total_time = (
        time.perf_counter()
        - wikipedia_total_start
    )

    # ========================================================
    # WIKIPEDIA TIMINGS
    # ========================================================

    print(
        "\n"
        + "-" * 70
    )

    print(
        "[TIMING] Wikipedia search requests: "
        f"{wikipedia_search_time:.2f} seconds"
    )

    print(
        "[TIMING] Wikipedia full-page downloads: "
        f"{wikipedia_page_time:.2f} seconds"
    )

    print(
        "[TIMING] Wikipedia page references: "
        f"{len(all_page_ids)}"
    )

    print(
        "[TIMING] Unique Wikipedia pages: "
        f"{len(set(all_page_ids))}"
    )

    print(
        "[TIMING] Text chunking: "
        f"{chunking_time:.2f} seconds"
    )

    print(
        "[TIMING] BGE semantic ranking: "
        f"{bge_time:.2f} seconds"
    )

    print(
        "[TIMING] Cross-Encoder reranking: "
        f"{cross_encoder_time:.2f} seconds"
    )

    print(
        "[TIMING] Wikipedia pipeline total: "
        f"{wikipedia_total_time:.2f} seconds"
    )

    # ========================================================
    # 10. ENTITY FILTER
    # ========================================================

    stage_start = (
        time.perf_counter()
    )

    wikipedia_shortlist = (
        filter_entity_mismatches(
            cleaned_claim,
            wikipedia_shortlist
        )
    )

    print_timing(
        "Entity filtering",
        stage_start
    )

    # ========================================================
    # 11. SCIENTIFIC RETRIEVAL
    # ========================================================

    scientific_start = (
        time.perf_counter()
    )

    if should_use_scientific_source(
        cleaned_claim
    ):

        scientific_results = (
            search_scientific_evidence(
                cleaned_claim,
                max_records=3
            )
        )

        for result in scientific_results:

            chunks = (
                split_into_chunks(
                    result[
                        "text"
                    ]
                )
            )

            for chunk in chunks:

                scientific_evidence.append({
                    "chunk_id": (
                        global_chunk_id
                    ),
                    "title": (
                        result[
                            "title"
                        ]
                    ),
                    "source": (
                        result[
                            "source"
                        ]
                    ),
                    "url": (
                        result[
                            "url"
                        ]
                    ),
                    "text": (
                        chunk
                    ),
                    "publication_id": (
                        result[
                            "publication_id"
                        ]
                    ),
                    "authors": (
                        result[
                            "authors"
                        ]
                    ),
                    "year": (
                        result[
                            "year"
                        ]
                    )
                })

                global_chunk_id += 1

    scientific_retrieval_time = (
        time.perf_counter()
        - scientific_start
    )

    print(
        "[TIMING] Scientific retrieval: "
        f"{scientific_retrieval_time:.2f} seconds"
    )

    # ========================================================
    # 12. SCIENTIFIC BGE
    # ========================================================

    stage_start = (
        time.perf_counter()
    )

    top_scientific = (
        rank_evidence(
            cleaned_claim,
            scientific_evidence,
            top_k=6
        )
    )

    scientific_bge_time = (
        time.perf_counter()
        - stage_start
    )

    print(
        "[TIMING] Scientific BGE ranking: "
        f"{scientific_bge_time:.2f} seconds"
    )

    # ========================================================
    # 13. SCIENTIFIC CROSS-ENCODER
    # ========================================================

    stage_start = (
        time.perf_counter()
    )

    reranked_scientific = (
        rerank_evidence(
            cleaned_claim,
            top_scientific,
            top_k=len(
                top_scientific
            )
        )
    )

    scientific_cross_time = (
        time.perf_counter()
        - stage_start
    )

    print(
        "[TIMING] Scientific Cross-Encoder: "
        f"{scientific_cross_time:.2f} seconds"
    )

    strong_scientific = [
        item
        for item
        in reranked_scientific
        if item[
            "reranker_score"
        ] > RERANKER_THRESHOLD
    ]

    # ========================================================
    # 14. COMBINE SOURCES
    # ========================================================

    combined_evidence = (
        wikipedia_shortlist
        + strong_scientific
    )

    # ========================================================
    # 15. COMPARISON REASONING
    # ========================================================

    stage_start = (
        time.perf_counter()
    )

    comparison_result = (
        reason_about_comparison(
            cleaned_claim,
            combined_evidence
        )
    )

    print_timing(
        "Comparison reasoning",
        stage_start
    )

    # ========================================================
    # 16. EVIDENCE DIVERSITY
    # ========================================================

    stage_start = (
        time.perf_counter()
    )

    diverse_evidence = (
        select_diverse_evidence(
            combined_evidence,
            top_k=5,
            max_per_document=1
        )
    )

    print_timing(
        "Evidence diversity",
        stage_start
    )

    # ========================================================
    # 17. BATCH NLI
    # ========================================================
    #
    # IMPORTANT:
    #
    # All evidence passages are now sent to DeBERTa together.
    #
    # There is NO loop calling DeBERTa individually.
    # ========================================================

    nli_total_start = (
        time.perf_counter()
    )

    evidence_texts = [
        item[
            "text"
        ]
        for item
        in diverse_evidence
    ]

    verification_results = (
        verify_claim_with_evidence_batch(
            cleaned_claim,
            evidence_texts
        )
    )

    verified_evidence = []

    for item, verification in zip(
        diverse_evidence,
        verification_results
    ):

        guarded_verification = (
            apply_factuality_guard(
                item[
                    "text"
                ],
                verification
            )
        )

        verified_item = (
            item.copy()
        )

        verified_item.update(
            guarded_verification
        )

        verified_evidence.append(
            verified_item
        )

    nli_total_time = (
        time.perf_counter()
        - nli_total_start
    )

    print(
        "[TIMING] NLI batch size: "
        f"{len(evidence_texts)}"
    )

    print(
        "[TIMING] NLI batch total: "
        f"{nli_total_time:.2f} seconds"
    )

    # ========================================================
    # 18. STRUCTURED COMPARISON RESULT
    # ========================================================

    if comparison_result is not None:

        comparison_verdict = (
            comparison_result[
                "verdict"
            ]
        )

        comparison_confidence = (
            comparison_result[
                "confidence"
            ]
        )

        comparison_reason = (
            comparison_result[
                "reason"
            ]
        )

        if (
            comparison_verdict
            == "SUPPORTED"
        ):

            support_score = (
                comparison_confidence
            )

            refute_score = 0.0

            insufficient_score = (
                1.0
                - comparison_confidence
            )

        else:

            support_score = 0.0

            refute_score = (
                comparison_confidence
            )

            insufficient_score = (
                1.0
                - comparison_confidence
            )

        explanation = (
            f'The claim "{cleaned_claim}" is '
            f'{comparison_verdict.lower()} by '
            f'comparative evidence. '
            f'{comparison_reason}'
        )

        total_time = (
            time.perf_counter()
            - total_start
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "[TIMING] TOTAL CLAIM TIME: "
            f"{total_time:.2f} seconds"
        )

        print(
            "=" * 70
            + "\n"
        )

        return {
            "received_claim": (
                cleaned_claim
            ),
            "explanation": (
                explanation
            ),
            "status": (
                "Claim processed successfully"
            ),
            "claim_domain": (
                claim_domain
            ),
            "final_verdict": (
                comparison_verdict
            ),
            "confidence": (
                comparison_confidence
            ),
            "support_score": (
                support_score
            ),
            "refute_score": (
                refute_score
            ),
            "insufficient_score": (
                insufficient_score
            ),
            "decision_margin": (
                comparison_confidence
            ),
            "decision_reason": (
                "Structured comparison reasoning "
                "matched explicit ranking or "
                "numeric evidence. "
                + comparison_reason
            ),
            "search_queries": (
                search_queries
            ),
            "evidence": (
                verified_evidence
            )
        }

    # ========================================================
    # 19. USABLE EVIDENCE
    # ========================================================

    usable_evidence = [
        item
        for item
        in verified_evidence
        if not item.get(
            "exclude_from_aggregation",
            False
        )
    ]

    # ========================================================
    # 20. EVIDENCE SUFFICIENCY
    # ========================================================

    (
        evidence_is_sufficient,
        sufficiency_reason
    ) = has_sufficient_evidence(
        usable_evidence,
        minimum_evidence=(
            MIN_STRONG_EVIDENCE
        )
    )

    if not evidence_is_sufficient:

        explanation = (
            generate_explanation(
                cleaned_claim,
                "INSUFFICIENT",
                verified_evidence
            )
        )

        total_time = (
            time.perf_counter()
            - total_start
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "[TIMING] TOTAL CLAIM TIME: "
            f"{total_time:.2f} seconds"
        )

        print(
            "=" * 70
            + "\n"
        )

        return {
            "received_claim": (
                cleaned_claim
            ),
            "explanation": (
                explanation
            ),
            "status": (
                "Insufficient strong evidence found"
            ),
            "claim_domain": (
                claim_domain
            ),
            "final_verdict": (
                "INSUFFICIENT"
            ),
            "confidence": 0.0,
            "support_score": 0.0,
            "refute_score": 0.0,
            "insufficient_score": 1.0,
            "decision_margin": 0.0,
            "decision_reason": (
                sufficiency_reason
            ),
            "search_queries": (
                search_queries
            ),
            "evidence": (
                verified_evidence
            )
        }

    # ========================================================
    # 21. VERDICT AGGREGATION
    # ========================================================

    final_result = (
        aggregate_verdict(
            verified_evidence
        )
    )

    # ========================================================
    # 22. EXPLANATION
    # ========================================================

    explanation = (
        generate_explanation(
            cleaned_claim,
            final_result[
                "final_verdict"
            ],
            verified_evidence
        )
    )

    # ========================================================
    # 23. TOTAL TIME
    # ========================================================

    total_time = (
        time.perf_counter()
        - total_start
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "[TIMING] TOTAL CLAIM TIME: "
        f"{total_time:.2f} seconds"
    )

    print(
        "=" * 70
        + "\n"
    )

    # ========================================================
    # 24. FINAL RESPONSE
    # ========================================================

    return {
        "received_claim": (
            cleaned_claim
        ),
        "explanation": (
            explanation
        ),
        "status": (
            "Claim processed successfully"
        ),
        "claim_domain": (
            claim_domain
        ),
        "final_verdict": (
            final_result[
                "final_verdict"
            ]
        ),
        "confidence": (
            final_result[
                "confidence"
            ]
        ),
        "support_score": (
            final_result[
                "support_score"
            ]
        ),
        "refute_score": (
            final_result[
                "refute_score"
            ]
        ),
        "insufficient_score": (
            final_result[
                "insufficient_score"
            ]
        ),
        "decision_margin": (
            final_result[
                "decision_margin"
            ]
        ),
        "decision_reason": (
            final_result[
                "decision_reason"
            ]
        ),
        "search_queries": (
            search_queries
        ),
        "evidence": (
            verified_evidence
        )
    }