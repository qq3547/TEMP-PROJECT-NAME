"""One-time interactive OAuth2 (PKCE) setup for the MAL API v2.

MAL only supports the "plain" PKCE method, so the code_challenge equals the
code_verifier itself (no SHA256 hashing) - non-standard vs most OAuth2 providers.
"""
import json
import secrets
import time
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs

import requests

from config import settings


def _generate_code_verifier(length: int = 100) -> str:
    return secrets.token_urlsafe(length)[:length]


def build_authorization_url(code_verifier: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.MAL_CLIENT_ID,
        "redirect_uri": settings.MAL_REDIRECT_URI,
        "code_challenge": code_verifier,
        "code_challenge_method": "plain",
    }
    return f"{settings.MAL_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"


def _extract_code(user_input: str) -> str:
    """Accept either a raw auth code or the full redirected URL."""
    if user_input.startswith("http"):
        query = parse_qs(urlparse(user_input).query)
        return query["code"][0]
    return user_input.strip()


def exchange_code_for_token(code: str, code_verifier: str) -> dict:
    data = {
        "client_id": settings.MAL_CLIENT_ID,
        "client_secret": settings.MAL_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "code_verifier": code_verifier,
        "redirect_uri": settings.MAL_REDIRECT_URI,
    }
    response = requests.post(settings.MAL_OAUTH_TOKEN_URL, data=data, timeout=30)
    response.raise_for_status()
    return response.json()


def refresh_access_token(refresh_token: str) -> dict:
    data = {
        "client_id": settings.MAL_CLIENT_ID,
        "client_secret": settings.MAL_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response = requests.post(settings.MAL_OAUTH_TOKEN_URL, data=data, timeout=30)
    response.raise_for_status()
    return response.json()


def save_tokens(token_response: dict) -> None:
    token_response["obtained_at"] = time.time()
    settings.TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings.TOKENS_PATH.write_text(json.dumps(token_response, indent=2))


def load_tokens() -> dict:
    if not settings.TOKENS_PATH.exists():
        raise FileNotFoundError(
            f"No tokens found at {settings.TOKENS_PATH}. Run `python main.py --auth` first."
        )
    return json.loads(settings.TOKENS_PATH.read_text())


def run_interactive_auth() -> None:
    if not settings.MAL_CLIENT_ID or not settings.MAL_CLIENT_SECRET:
        raise RuntimeError(
            "MAL_CLIENT_ID / MAL_CLIENT_SECRET are not set. Register an app at "
            "https://myanimelist.net/apiconfig and populate .env first."
        )

    code_verifier = _generate_code_verifier()
    auth_url = build_authorization_url(code_verifier)

    print("Open this URL, authorize the app, then paste the resulting redirect URL "
          "(or just the 'code' value) back here:\n")
    print(auth_url)
    webbrowser.open(auth_url)

    user_input = input("\nRedirect URL or code: ")
    code = _extract_code(user_input)

    token_response = exchange_code_for_token(code, code_verifier)
    save_tokens(token_response)
    print(f"Tokens saved to {settings.TOKENS_PATH}")


if __name__ == "__main__":
    run_interactive_auth()
