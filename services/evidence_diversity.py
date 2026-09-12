def select_diverse_evidence(
    ranked_evidence: list[dict],
    top_k: int = 5,
    max_per_document: int = 2
) -> list[dict]:

    selected = []

    document_counts = {}

    for item in ranked_evidence:

        if item["source"] == "Wikipedia":

            document_key = (
                "Wikipedia",
                item.get("page_id")
            )

        elif item["source"] == "Scientific":

            document_key = (
                "Scientific",
                item.get("publication_id")
            )

        else:

            document_key = (
                item.get("source", "Unknown"),
                item.get("url", "")
            )

        current_count = document_counts.get(
            document_key,
            0
        )

        if current_count >= max_per_document:
            continue

        selected.append(item)

        document_counts[document_key] = (
            current_count + 1
        )

        if len(selected) >= top_k:
            break

    return selected