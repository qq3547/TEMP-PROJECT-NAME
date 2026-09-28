"""CLI orchestrator for the MAL anime ETL pipeline."""
import argparse
import logging

from config import settings


def _setup_logging() -> None:
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.LOGS_DIR / "pipeline.log"),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="MAL anime ETL pipeline")
    parser.add_argument("--auth", action="store_true", help="Run one-time MAL OAuth2 setup")
    parser.add_argument("--extract", action="store_true", help="Crawl MAL API into MongoDB")
    parser.add_argument("--transform", action="store_true", help="Clean Mongo data and load into Postgres")
    parser.add_argument("--load-sql", action="store_true", help="Transform Mongo data and load it into Postgres")
    parser.add_argument("--all", action="store_true", help="Run extract + transform in sequence")
    parser.add_argument("--max-id", type=int, default=settings.MAX_ANIME_ID, help="Highest MAL anime ID to crawl")
    args = parser.parse_args()

    _setup_logging()

    if not any([args.auth, args.extract, args.transform, args.load_sql, args.all]):
        parser.print_help()
        return

    if args.auth:
        from extract import mal_auth
        mal_auth.run_interactive_auth()

    if args.extract or args.all:
        from extract.extract_runner import run_extract
        run_extract(max_id=args.max_id)

    if args.transform or args.load_sql or args.all:
        from transform.transform_runner import build_dataframes
        from load_sql.sql_loader import load_all
        load_all(build_dataframes())


if __name__ == "__main__":
    main()