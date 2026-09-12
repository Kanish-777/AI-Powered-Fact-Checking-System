import time
import requests


GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def search_news(claim: str, max_records: int = 10) -> list[dict]:

    params = {
        "query": f'{claim} sourcelang:english',
        "mode": "artlist",
        "format": "json",
        "maxrecords": max_records,
        "timespan": "3months"
    }

    for attempt in range(3):

        try:
            response = requests.get(
                GDELT_API_URL,
                params=params,
                timeout=20
            )

            if response.status_code == 429:

                if attempt < 2:
                    time.sleep(5)
                    continue

                return []

            response.raise_for_status()

            data = response.json()

            results = []

            for article in data.get("articles", []):

                results.append({
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "domain": article.get("domain", ""),
                    "language": article.get("language", ""),
                    "published_at": article.get("seendate", ""),
                    "source": "News"
                })

            return results

        except requests.exceptions.Timeout:

            if attempt < 2:
                time.sleep(3)
                continue

            return []

        except requests.exceptions.RequestException:

            return []

    return []