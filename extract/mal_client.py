"""Thin client around the MAL API v2 with automatic token refresh."""
import logging
import time

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import settings
from extract import mal_auth

logger = logging.getLogger(__name__)


class RateLimitedError(Exception):
    pass


class TransientAPIError(Exception):
    pass


class AnimeNotFoundError(Exception):
    pass


class MALClient:
    def __init__(self):
        self._tokens = mal_auth.load_tokens()
        self._session = requests.Session()

    def _token_expires_at(self) -> float:
        return self._tokens["obtained_at"] + self._tokens.get("expires_in", 0)

    def _ensure_valid_token(self) -> None:
        # refresh a little early to avoid edge-of-expiry failures
        if time.time() >= self._token_expires_at() - 60:
            refreshed = mal_auth.refresh_access_token(self._tokens["refresh_token"])
            mal_auth.save_tokens(refreshed)
            self._tokens = refreshed

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._tokens['access_token']}"}

    @retry(
        retry=retry_if_exception_type((
            RateLimitedError,
            TransientAPIError,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        )),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        stop=stop_after_attempt(6),
        reraise=True,
    )
    def get_anime(self, anime_id: int, fields: str = settings.ANIME_FIELDS) -> dict:
        self._ensure_valid_token()
        url = f"{settings.MAL_API_BASE}/anime/{anime_id}"
        response = self._session.get(
            url, headers=self._headers(), params={"fields": fields}, timeout=(10, 60)
        )

        if response.status_code == 404:
            raise AnimeNotFoundError(f"anime_id={anime_id} not found")
        if response.status_code == 429:
            raise RateLimitedError(f"rate limited on anime_id={anime_id}")
        if response.status_code >= 500:
            raise TransientAPIError(f"server error {response.status_code} on anime_id={anime_id}")
        response.raise_for_status()
        return response.json()
