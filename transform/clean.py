"""Cleans and flattens a single raw MAL anime document into relational rows."""
from datetime import date
from typing import Optional


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    parts = value.split("-")
    try:
        if len(parts) == 3:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
        if len(parts) == 2:
            return date(int(parts[0]), int(parts[1]), 1)
        if len(parts) == 1:
            return date(int(parts[0]), 1, 1)
    except ValueError:
        return None
    return None


def clean_anime_row(doc: dict) -> dict:
    return {
        "mal_id": doc["id"],
        "title": doc.get("title"),
        "media_type": doc.get("media_type"),
        "status": doc.get("status"),
        "start_date": _parse_date(doc.get("start_date")),
        "end_date": _parse_date(doc.get("end_date")),
        "mean_score": doc.get("mean"),
        "rank": doc.get("rank"),
        "popularity": doc.get("popularity"),
        "num_list_users": doc.get("num_list_users"),
        "num_scoring_users": doc.get("num_scoring_users"),
        "num_episodes": doc.get("num_episodes"),
        "source": doc.get("source"),
        "rating": doc.get("rating"),
        "average_episode_duration": doc.get("average_episode_duration"),
        "nsfw": doc.get("nsfw"),
        "synopsis": doc.get("synopsis"),
        "start_season_year": (doc.get("start_season") or {}).get("year"),
        "start_season_season": (doc.get("start_season") or {}).get("season"),
    }


def extract_genres(doc: dict) -> list[dict]:
    return [{"genre_id": g["id"], "name": g["name"]} for g in doc.get("genres", [])]


def extract_anime_genres(doc: dict) -> list[dict]:
    return [{"mal_id": doc["id"], "genre_id": g["id"]} for g in doc.get("genres", [])]


def extract_studios(doc: dict) -> list[dict]:
    return [{"studio_id": s["id"], "name": s["name"]} for s in doc.get("studios", [])]


def extract_anime_studios(doc: dict) -> list[dict]:
    return [{"mal_id": doc["id"], "studio_id": s["id"]} for s in doc.get("studios", [])]
