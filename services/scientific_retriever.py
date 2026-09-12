import re
import requests


EUROPE_PMC_API_URL = (
    "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
)


def clean_html(text: str) -> str:
    clean_text = re.sub(r"<[^>]+>", " ", text)
    clean_text = re.sub(r"\s+", " ", clean_text)

    return clean_text.strip()


def search_scientific_evidence(
    claim: str,
    max_records: int = 5
) -> list[dict]:

    params = {
        "query": claim,
        "format": "json",
        "resultType": "core",
        "pageSize": max_records
    }

    try:
        response = requests.get(
            EUROPE_PMC_API_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        results = []

        publications = (
            data
            .get("resultList", {})
            .get("result", [])
        )

        for publication in publications:

            abstract = clean_html(
                publication.get(
                    "abstractText",
                    ""
                )
            )

            if not abstract:
                continue

            publication_id = publication.get(
                "id",
                ""
            )

            source_id = publication.get(
                "source",
                ""
            )

            results.append({
                "title": publication.get(
                    "title",
                    ""
                ),
                "text": abstract,
                "publication_id": publication_id,
                "publication_source": source_id,
                "journal": publication.get(
                    "journalTitle",
                    ""
                ),
                "authors": publication.get(
                    "authorString",
                    ""
                ),
                "year": publication.get(
                    "pubYear",
                    ""
                ),
                "source": "Scientific",
                "url": (
                    f"https://europepmc.org/article/"
                    f"{source_id}/{publication_id}"
                )
            })

        return results

    except requests.exceptions.RequestException:
        return []