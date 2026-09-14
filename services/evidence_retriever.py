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
# INTERACTIVE RETRIEVAL SETTINGS
# ============================================================

# We do NOT allow Wikipedia to block a user request for
# 30-60+ seconds.
MAX_RATE_LIMIT_WAIT = 3

# Keep retries small because this is an interactive application.
MAX_RETRIES = 2

# Separate connection/read timeout.
REQUEST_TIMEOUT = (4, 8)


# ============================================================
# WIKIPEDIA REQUEST
# ============================================================

def make_wikipedia_request(
    params: dict,
    max_retries: int = MAX_RETRIES
) -> dict:

    for attempt in range(max_retries):

        try:

            response = requests.get(
                WIKIPEDIA_API_URL,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT
            )

            # ------------------------------------------------
            # RATE LIMIT
            # ------------------------------------------------

            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After"
                )

                try:
                    wait_time = int(retry_after) if retry_after else 1

                except (ValueError, TypeError):
                    wait_time = 1

                # --------------------------------------------
                # IMPORTANT:
                # Never freeze the web request for ~1 minute.
                #
                # If Wikipedia asks us to wait too long,
                # fail this retrieval gracefully instead.
                # --------------------------------------------

                if wait_time > MAX_RATE_LIMIT_WAIT:

                    print(
                        "Wikipedia rate limited this request. "
                        f"Retry-After={wait_time}s. "
                        "Skipping instead of blocking the user."
                    )

                    return {}

                if attempt < max_retries - 1:

                    print(
                        "Wikipedia rate limit reached. "
                        f"Retrying after {wait_time}s..."
                    )

                    time.sleep(wait_time)

                    continue

                return {}

            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:

            print(
                "Wikipedia request timed out."
            )

            if attempt < max_retries - 1:

                time.sleep(1)

                continue

            return {}

        except requests.exceptions.RequestException as error:

            print(
                "Wikipedia request failed: "
                f"{error}"
            )

            if attempt < max_retries - 1:

                time.sleep(1)

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
    # Deduplicate pages.
    # --------------------------------------------------------

    unique_page_ids = list(
        dict.fromkeys(
            page_ids
        )
    )

    results = {}

    # --------------------------------------------------------
    # Keep concurrency conservative.
    #
    # Two simultaneous requests are enough for responsiveness
    # while reducing unnecessary pressure on Wikipedia.
    # --------------------------------------------------------

    max_workers = min(
        2,
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