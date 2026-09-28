"""Central configuration loaded from environment / .env."""
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
TOKENS_PATH = BASE_DIR / "config" / "tokens.json"
LOGS_DIR = BASE_DIR / "logs"

MAL_CLIENT_ID = os.getenv("MAL_CLIENT_ID", "")
MAL_CLIENT_SECRET = os.getenv("MAL_CLIENT_SECRET", "")
MAL_REDIRECT_URI = os.getenv("MAL_REDIRECT_URI", "http://localhost:8080/callback")
MAL_API_BASE = "https://api.myanimelist.net/v2"
MAL_OAUTH_AUTHORIZE_URL = "https://myanimelist.net/v1/oauth2/authorize"
MAL_OAUTH_TOKEN_URL = "https://myanimelist.net/v1/oauth2/token"

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "mal_raw")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mal_anime")
POSTGRES_USER = os.getenv("POSTGRES_USER", "mal_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mal_password")
POSTGRES_URI = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

MAX_ANIME_ID = int(os.getenv("MAX_ANIME_ID", "60000"))
REQUEST_DELAY_SECONDS = float(os.getenv("REQUEST_DELAY_SECONDS", "1.0"))
USE_JIKAN_ID_DISCOVERY = os.getenv("USE_JIKAN_ID_DISCOVERY", "false").lower() == "true"

# Fields requested from GET /anime/{id}
ANIME_FIELDS = ",".join(
    [
        "id",
        "title",
        "alternative_titles",
        "start_date",
        "end_date",
        "synopsis",
        "mean",
        "rank",
        "popularity",
        "num_list_users",
        "num_scoring_users",
        "nsfw",
        "created_at",
        "updated_at",
        "media_type",
        "status",
        "genres",
        "num_episodes",
        "start_season",
        "source",
        "average_episode_duration",
        "rating",
        "studios",
    ]
)
