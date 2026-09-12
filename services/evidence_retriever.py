import time
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "AIFactCheckingSystem/1.0 "
        "(academic student project)"
    )
}


# ============================================================
# WIKIPEDIA REQUEST
# ============================================================

def make_wikipedia_request(
    params: dict,
    max_retries: int = 4
) -> dict:

    for attempt in range(max_retries):

        try:

            response = requests.get(
                WIKIPEDIA_API_URL,
                params=params,
                headers=HEADERS,
                timeout=15
            )

            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After"
                )

                if retry_after:

                    try:
                        wait_time = int(retry_after)

                    except ValueError:
                        wait_time = 3 * (2 ** attempt)

                else:
                    wait_time = 3 * (2 ** attempt)

                print(
                    "Wikipedia rate limit reached. "
                    f"Waiting {wait_time} seconds..."
                )

                time.sleep(wait_time)

                continue

            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:

            if attempt < max_retries - 1:

                wait_time = 2 * (2 ** attempt)

                time.sleep(wait_time)

                continue

            return {}

        except requests.exceptions.RequestException:

            if attempt < max_retries - 1:

                time.sleep(2)

                continue

            return {}

    return {}


# ============================================================
# WIKIPEDIA SEARCH
# ============================================================

@lru_cache(maxsize=200)
def search_wikipedia(
    claim: str,
    limit: int = 5
):

    params = {
        "action": "query",
        "list": "search",
        "srsearch": claim,
        "format": "json",
        "utf8": 1,
        "srlimit": limit
    }

    data = make_wikipedia_request(
        params
    )

    results = []

    search_items = (
        data
        .get("query", {})
        .get("search", [])
    )

    for item in search_items:

        results.append({
            "title": item["title"],
            "page_id": item["pageid"],
            "snippet": item.get(
                "snippet",
                ""
            ),
            "source": "Wikipedia",
            "url": (
                "https://en.wikipedia.org/"
                f"?curid={item['pageid']}"
            )
        })

    return results


# ============================================================
# SINGLE FULL WIKIPEDIA PAGE
# ============================================================

@lru_cache(maxsize=300)
def get_wikipedia_page_text(
    page_id: int
) -> str:

    params = {
        "action": "query",
        "pageids": page_id,
        "prop": "extracts",
        "explaintext": 1,
        "format": "json"
    }

    data = make_wikipedia_request(
        params
    )

    page = (
        data
        .get("query", {})
        .get("pages", {})
        .get(
            str(page_id),
            {}
        )
    )

    return page.get(
        "extract",
        ""
    )


# ============================================================
# MULTIPLE FULL WIKIPEDIA PAGES
# ============================================================

def get_wikipedia_pages_text(
    page_ids: list[int]
) -> dict[int, str]:

    if not page_ids:
        return {}

    # --------------------------------------------------------
    # Deduplicate downloads only.
    #
    # A page can still later be evaluated under several
    # different search queries.
    # --------------------------------------------------------

    unique_page_ids = list(
        dict.fromkeys(
            page_ids
        )
    )

    results = {}

    # --------------------------------------------------------
    # Only 3 simultaneous requests.
    #
    # This reduces waiting time without aggressively hitting
    # Wikipedia with too many requests.
    # --------------------------------------------------------

    max_workers = min(
        3,
        len(unique_page_ids)
    )

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        future_to_page_id = {
            executor.submit(
                get_wikipedia_page_text,
                page_id
            ): page_id

            for page_id in unique_page_ids
        }

        for future in as_completed(
            future_to_page_id
        ):

            page_id = (
                future_to_page_id[
                    future
                ]
            )

            try:

                page_text = (
                    future.result()
                )

            except Exception as error:

                print(
                    "Wikipedia retrieval error "
                    f"for page {page_id}: "
                    f"{error}"
                )

                page_text = ""

            results[
                page_id
            ] = page_text

    return results