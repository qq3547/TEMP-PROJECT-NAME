"""Crawls the MAL anime catalog by sequential ID and stages raw JSON in MongoDB.

The official MAL API has no bulk "list all anime" endpoint, so this walks
anime IDs from the last checkpoint up to MAX_ANIME_ID, fetching each one
individually and skipping IDs that 404 (gaps/deleted entries).
"""
import logging
import time

from tqdm import tqdm

from config import settings
from extract.mal_client import AnimeNotFoundError, MALClient
from load_raw import mongo_loader

logger = logging.getLogger(__name__)


def run_extract(max_id: int = settings.MAX_ANIME_ID, delay: float = settings.REQUEST_DELAY_SECONDS) -> None:
    client = MALClient()
    start_id = mongo_loader.get_checkpoint() + 1

    if start_id > max_id:
        logger.info("Checkpoint (%s) already past max_id (%s), nothing to do.", start_id - 1, max_id)
        return

    if settings.USE_JIKAN_ID_DISCOVERY:
        from extract import jikan_discovery
        id_iter = [i for i in jikan_discovery.get_valid_ids() if start_id <= i <= max_id]
    else:
        id_iter = range(start_id, max_id + 1)

    fetched, not_found = 0, 0
    for anime_id in tqdm(id_iter, desc="Extracting anime"):
        try:
            doc = client.get_anime(anime_id)
            mongo_loader.upsert_anime(doc)
            fetched += 1
        except AnimeNotFoundError:
            not_found += 1
        except Exception:
            logger.exception("Failed on anime_id=%s, stopping so it can be resumed", anime_id)
            mongo_loader.set_checkpoint(anime_id - 1)
            raise
        finally:
            time.sleep(delay)

        mongo_loader.set_checkpoint(anime_id)

    logger.info("Extract complete: %s fetched, %s not found (up to id %s)", fetched, not_found, max_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_extract()
