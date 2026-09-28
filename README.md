# MAL Anime ETL Pipeline

An end-to-end ETL project that pulls anime metadata from the official MyAnimeList (MAL) API, stages the raw JSON in MongoDB, cleans and transforms it into a relational schema, loads it into PostgreSQL, and analyzes/visualizes the results in a Jupyter notebook.

## Pipeline overview

```
MAL API v2 (OAuth2)
      │  GET /anime/{id}, sequential ID crawl
      ▼
MongoDB  (raw_anime, meta/checkpoint collections)
      │  clean + flatten (transform/clean.py)
      ▼
PostgreSQL (anime, genres, anime_genres, studios, anime_studios)
      │  SQL analytics (analysis/queries.py)
      ▼
Jupyter notebook (notebook/visualize.ipynb) — charts + tables
```

All stages are orchestrated by a single CLI entry point, [main.py](main.py), and both databases run locally via Docker Compose.

## Why a sequential ID crawl?

The official MAL API v2 has no "list all anime" endpoint — `/anime` requires a search keyword, and `/anime/ranking` is capped at a few hundred results per ranking type. To reach broad catalog coverage, the extractor walks every MAL ID from `1` up to `MAX_ANIME_ID` (~60,000) via `GET /anime/{id}`, skipping IDs that 404 (gaps, deleted entries, etc.). At a conservative ~1 request/second this takes many hours, so the crawl is checkpointed in MongoDB and safely resumable if interrupted.

An optional Jikan-based ID-discovery optimization exists (`extract/jikan_discovery.py`, toggled via `USE_JIKAN_ID_DISCOVERY` in `.env`) to pre-filter out known-invalid IDs and reduce wasted requests. It's disabled by default because the public Jikan API proved unreliable (intermittent 504s) during development; the official-API-only crawl is the default, reliable path.

## Tech stack

| Layer | Technology |
|---|---|
| Extraction | Python, `requests`, OAuth2 (PKCE), `tenacity` for retry/backoff |
| Raw staging | MongoDB (`pymongo`) |
| Transform | `pandas` |
| Relational store | PostgreSQL, SQLAlchemy ORM |
| Analysis | SQL (via SQLAlchemy), `pandas` |
| Visualization | Jupyter, `matplotlib`, `seaborn` |
| Infra | Docker Compose (Mongo + Postgres), Python virtual environment |

## Project structure

```
main.py                  CLI orchestrator (--auth, --extract, --transform, --load-sql, --all)
config/settings.py       Central config loaded from .env
extract/                 MAL OAuth2 flow, API client, ID crawler, optional Jikan discovery
load_raw/                MongoDB persistence + crawl checkpointing
transform/               Clean/flatten raw MAL JSON into relational rows
load_sql/                SQLAlchemy schema + upsert loader for PostgreSQL
analysis/queries.py      Parametrized analytical SQL queries
notebook/visualize.ipynb Visualization report over the loaded PostgreSQL data
docker-compose.yml       MongoDB + PostgreSQL services
requirements.txt         Python dependencies
```

## Prerequisites

- Python 3.11+ and a virtual environment
- Docker Desktop (for MongoDB + PostgreSQL)
- A MyAnimeList account and a registered API app at [myanimelist.net/apiconfig](https://myanimelist.net/apiconfig) (Web app type) to obtain a client ID and secret

## Setup

1. **Clone and create a virtual environment**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **Configure environment variables**
   ```powershell
   Copy-Item .env.example .env
   ```
   Edit `.env` and fill in `MAL_CLIENT_ID` / `MAL_CLIENT_SECRET` from your registered MAL app. Adjust `MAX_ANIME_ID`, `REQUEST_DELAY_SECONDS`, or database credentials if needed.
3. **Start MongoDB and PostgreSQL**
   ```powershell
   docker compose up -d
   ```
4. **Authenticate with MAL (one-time)**
   ```powershell
   python main.py --auth
   ```
   This opens a browser for the OAuth2 authorization-code (PKCE) flow and saves tokens to `config/tokens.json` (gitignored). The client auto-refreshes the access token afterward.

## Running the pipeline

```powershell
# Crawl the MAL catalog into MongoDB (resumable; safe to stop/restart)
python main.py --extract

# Try a small range first to validate everything end-to-end
python main.py --extract --max-id 50

# Clean, transform, and load the staged data into PostgreSQL
python main.py --load-sql

# Or run extract + load in one go
python main.py --all
```

Then open [notebook/visualize.ipynb](notebook/visualize.ipynb) and run all cells to generate the analysis and charts against the PostgreSQL data.

## Data model

| Table | Description |
|---|---|
| `anime` | Core metadata: title, media type, status, dates, score, rank, popularity, episode count, source, rating, synopsis |
| `genres` / `anime_genres` | Genre lookup + many-to-many junction |
| `studios` / `anime_studios` | Studio lookup + many-to-many junction |

MongoDB stores the raw API response per anime (`raw_anime` collection) plus a crawl checkpoint (`meta` collection) so the extractor can resume without duplicating work or re-fetching completed IDs.

## Analysis & visualization

[analysis/queries.py](analysis/queries.py) provides parametrized SQL helpers for: dataset coverage, release trends by year/season, score profiles by format/genre/studio/source/rating, episode-band comparisons, an audience-size-vs-score sample, and a vote-filtered top-ranked title list.

[notebook/visualize.ipynb](notebook/visualize.ipynb) turns those into a narrative report — catalog release trends, score distributions and category comparisons, audience engagement vs. score, studio output and quality, and a highest-ranked titles table.

## Known limitations

- **Snapshot data, not history.** MAL scores, ranks, and popularity are captured at extraction time; the schema has no historical time series for these fields.
- **Sample-size sensitivity.** Genre/studio/format score comparisons use minimum-count thresholds to avoid over-interpreting small groups.
- **Many-to-many credits.** An anime can have multiple genres/studios; counts use `COUNT(DISTINCT anime.mal_id)` to avoid double-counting.
- **Rate limits are estimated.** The official MAL API's rate limit isn't formally documented; the crawler defaults to a conservative delay, tunable via `REQUEST_DELAY_SECONDS`.

## Security notes

- `.env`, `config/tokens.json`, and Jikan ID-cache files are gitignored — never commit real credentials or tokens.
- If a MAL access/refresh token is ever exposed (e.g. pasted into a chat, shared log, or screenshot), revoke and regenerate it from your MAL account settings.
