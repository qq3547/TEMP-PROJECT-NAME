"""Reads raw anime docs from MongoDB and builds DataFrames ready for SQL loading."""
import logging

import pandas as pd

from load_raw import mongo_loader
from transform.clean import (
    clean_anime_row,
    extract_anime_genres,
    extract_anime_studios,
    extract_genres,
    extract_studios,
)

logger = logging.getLogger(__name__)


def build_dataframes() -> dict[str, pd.DataFrame]:
    anime_rows, genre_rows, anime_genre_rows, studio_rows, anime_studio_rows = [], [], [], [], []

    for doc in mongo_loader.iter_raw_anime():
        anime_rows.append(clean_anime_row(doc))
        genre_rows.extend(extract_genres(doc))
        anime_genre_rows.extend(extract_anime_genres(doc))
        studio_rows.extend(extract_studios(doc))
        anime_studio_rows.extend(extract_anime_studios(doc))

    anime_df = pd.DataFrame(anime_rows).drop_duplicates(subset=["mal_id"])
    genres_df = pd.DataFrame(genre_rows).drop_duplicates(subset=["genre_id"])
    anime_genres_df = pd.DataFrame(anime_genre_rows).drop_duplicates()
    studios_df = pd.DataFrame(studio_rows).drop_duplicates(subset=["studio_id"])
    anime_studios_df = pd.DataFrame(anime_studio_rows).drop_duplicates()

    logger.info(
        "Transformed %s anime, %s genres, %s studios",
        len(anime_df), len(genres_df), len(studios_df),
    )
    return {
        "anime": anime_df,
        "genres": genres_df,
        "anime_genres": anime_genres_df,
        "studios": studios_df,
        "anime_studios": anime_studios_df,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    frames = build_dataframes()
    for name, df in frames.items():
        print(name, df.shape)
