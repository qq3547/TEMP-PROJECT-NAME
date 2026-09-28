"""MongoDB persistence for raw MAL API responses and crawl checkpointing."""
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.collection import Collection

from config import settings

_client = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGO_URI)
    return _client


def get_db():
    return get_client()[settings.MONGO_DB_NAME]


def raw_anime_collection() -> Collection:
    return get_db()["raw_anime"]


def meta_collection() -> Collection:
    return get_db()["meta"]


def upsert_anime(doc: dict) -> None:
    doc = dict(doc)
    doc["_id"] = doc["id"]
    doc["fetched_at"] = datetime.now(timezone.utc)
    raw_anime_collection().replace_one({"_id": doc["_id"]}, doc, upsert=True)


def get_checkpoint() -> int:
    record = meta_collection().find_one({"_id": "extract_checkpoint"})
    return record["last_id"] if record else 0


def set_checkpoint(last_id: int) -> None:
    meta_collection().update_one(
        {"_id": "extract_checkpoint"},
        {"$set": {"last_id": last_id}},
        upsert=True,
    )


def count_raw_anime() -> int:
    return raw_anime_collection().count_documents({})


def iter_raw_anime():
    return raw_anime_collection().find({})
