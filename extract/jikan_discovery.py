"""One-time helper to enumerate valid MAL anime IDs via the unofficial Jikan API.

Jikan is only ever used here to discover which IDs exist; all actual anime
data still comes from the official MAL API. This avoids wasting official API
calls on gap/deleted IDs during the sequential crawl.
"""
import json
import logging
import time

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = logging.getLogger(__name__)

JIKAN_ANIME_URL = "https://api.jikan.moe/v4/anime"
CACHE_PATH = settings.BASE_DIR / "config" / "valid_ids.json"
PROGRESS_PATH = settings.BASE_DIR / "config" / "valid_ids_progress.json"
REQUEST_DELAY = 0.4  # Jikan v4 allows ~3 req/sec unauthenticated


@retry(wait=wait_exponential(multiplier=2, min=2, max=60), stop=stop_after_attempt(6), reraise=True)
def _fetch_page(page: int) -> dict:
    response = requests.get(
        JIKAN_ANIME_URL,
        params={"page": page, "order_by": "mal_id", "sort": "asc"},
        timeout=(10, 60),
    )
    response.raise_for_status()
    return response.json()


def _fetch_all_ids() -> list[int]:
    if PROGRESS_PATH.exists():
        progress = json.loads(PROGRESS_PATH.read_text())
        ids, page = progress["ids"], progress["next_page"]
        logger.info("Resuming ID discovery from page %s (%s ids so far)", page, len(ids))
    else:
        ids, page = [], 1

    while True:
        payload = _fetch_page(page)
        ids.extend(item["mal_id"] for item in payload.get("data", []))
        pagination = payload.get("pagination", {})
        has_next = pagination.get("has_next_page")
        PROGRESS_PATH.write_text(json.dumps({"ids": ids, "next_page": page + 1}))
        if not has_next:
            break
        page += 1
        time.sleep(REQUEST_DELAY)

    PROGRESS_PATH.unlink(missing_ok=True)
    return sorted(set(ids))


def get_valid_ids() -> list[int]:
    """Returns the cached ID list if present, otherwise fetches and caches it."""
    if CACHE_PATH.exists():
        logger.info("Loading cached valid ID list from %s", CACHE_PATH)
        return json.loads(CACHE_PATH.read_text())

    logger.info("Fetching full valid anime ID list from Jikan (one-time)...")
    ids = _fetch_all_ids()
    CACHE_PATH.write_text(json.dumps(ids))
    logger.info("Cached %s valid anime IDs to %s", len(ids), CACHE_PATH)
    return ids
