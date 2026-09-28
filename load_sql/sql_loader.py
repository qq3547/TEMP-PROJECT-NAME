"""Creates the Postgres schema and bulk-upserts transformed DataFrames into it."""
import logging

import pandas as pd
from sqlalchemy import Engine, Table, create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert

from config import settings
from load_sql.schema import Base

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    return create_engine(settings.POSTGRES_URI)


def init_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def _upsert_dataframe(engine: Engine, table: Table, df: pd.DataFrame) -> None:
    if df.empty:
        return
    records = df.astype(object).where(pd.notnull(df), None).to_dict(orient="records")
    pk_columns = [c.name for c in table.primary_key.columns]
    update_columns = {c.name: c for c in table.columns if c.name not in pk_columns}

    with engine.begin() as conn:
        for i in range(0, len(records), 1000):
            batch = records[i : i + 1000]
            stmt = pg_insert(table).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=pk_columns,
                set_={name: stmt.excluded[name] for name in update_columns},
            ) if update_columns else stmt.on_conflict_do_nothing(index_elements=pk_columns)
            conn.execute(stmt)


def load_all(frames: dict[str, pd.DataFrame]) -> None:
    engine = get_engine()
    init_schema(engine)

    # parents before junction tables, to satisfy FK constraints
    _upsert_dataframe(engine, Base.metadata.tables["anime"], frames["anime"])
    _upsert_dataframe(engine, Base.metadata.tables["genres"], frames["genres"])
    _upsert_dataframe(engine, Base.metadata.tables["studios"], frames["studios"])
    _upsert_dataframe(engine, Base.metadata.tables["anime_genres"], frames["anime_genres"])
    _upsert_dataframe(engine, Base.metadata.tables["anime_studios"], frames["anime_studios"])

    logger.info("Loaded all frames into Postgres at %s", settings.POSTGRES_HOST)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from transform.transform_runner import build_dataframes

    load_all(build_dataframes())
