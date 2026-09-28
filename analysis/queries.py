"""Analytical SQL queries against the cleaned Postgres anime store."""
import pandas as pd
from sqlalchemy import Engine


def dataset_overview(engine: Engine) -> pd.DataFrame:
    query = """
        SELECT COUNT(*) AS anime_count,
               COUNT(mean_score) AS scored_count,
               COUNT(start_season_year) AS dated_count,
               COUNT(num_episodes) AS episode_count,
               COUNT(num_list_users) AS audience_count,
               ROUND(AVG(mean_score)::numeric, 3) AS mean_score,
               ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mean_score))::numeric, 3)
                   AS median_score,
               MIN(start_season_year) AS first_release_year,
               MAX(start_season_year) AS last_release_year
        FROM anime
    """
    return pd.read_sql(query, engine)


def catalog_by_year(engine: Engine) -> pd.DataFrame:
    query = """
        SELECT start_season_year AS year,
               media_type,
               COUNT(*) AS anime_count,
               COUNT(mean_score) AS scored_count,
               ROUND(AVG(mean_score)::numeric, 3) AS avg_score
        FROM anime
        WHERE start_season_year IS NOT NULL
        GROUP BY start_season_year, media_type
        ORDER BY year, media_type
    """
    return pd.read_sql(query, engine)


def seasonal_catalog(engine: Engine) -> pd.DataFrame:
    query = """
        SELECT start_season_year AS year,
               start_season_season AS season,
               COUNT(*) AS anime_count,
               COUNT(mean_score) AS scored_count,
               ROUND(AVG(mean_score)::numeric, 3) AS avg_score
        FROM anime
        WHERE start_season_year IS NOT NULL
          AND start_season_season IS NOT NULL
        GROUP BY start_season_year, start_season_season
        ORDER BY year,
                 CASE start_season_season
                     WHEN 'winter' THEN 1 WHEN 'spring' THEN 2
                     WHEN 'summer' THEN 3 WHEN 'fall' THEN 4 ELSE 5
                 END
    """
    return pd.read_sql(query, engine)


def media_type_score_profile(engine: Engine, min_count: int = 30) -> pd.DataFrame:
    query = """
        SELECT media_type,
               COUNT(*) AS anime_count,
               COUNT(mean_score) AS scored_count,
               ROUND(AVG(mean_score)::numeric, 3) AS mean_score,
               ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mean_score))::numeric, 3)
                   AS median_score,
               ROUND((PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY mean_score))::numeric, 3)
                   AS q1_score,
               ROUND((PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY mean_score))::numeric, 3)
                   AS q3_score,
               ROUND((SUM(mean_score * num_scoring_users)
                      / NULLIF(SUM(num_scoring_users), 0))::numeric, 3) AS weighted_score
        FROM anime
        WHERE media_type IS NOT NULL
        GROUP BY media_type
        HAVING COUNT(mean_score) >= %(min_count)s
        ORDER BY scored_count DESC
    """
    return pd.read_sql(query, engine, params={"min_count": min_count})


def genre_score_profile(engine: Engine, min_count: int = 100) -> pd.DataFrame:
    query = """
        SELECT g.name AS genre,
               COUNT(DISTINCT a.mal_id) AS anime_count,
               COUNT(DISTINCT a.mal_id) FILTER (WHERE a.mean_score IS NOT NULL) AS scored_count,
               ROUND(AVG(a.mean_score)::numeric, 3) AS mean_score,
               ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY a.mean_score))::numeric, 3)
                   AS median_score,
               ROUND((PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY a.mean_score))::numeric, 3)
                   AS q1_score,
               ROUND((PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY a.mean_score))::numeric, 3)
                   AS q3_score,
               ROUND((SUM(a.mean_score * a.num_scoring_users)
                      / NULLIF(SUM(a.num_scoring_users), 0))::numeric, 3) AS weighted_score
        FROM genres g
        JOIN anime_genres ag ON ag.genre_id = g.genre_id
        JOIN anime a ON a.mal_id = ag.mal_id
        GROUP BY g.genre_id, g.name
        HAVING COUNT(a.mean_score) >= %(min_count)s
        ORDER BY median_score DESC
    """
    return pd.read_sql(query, engine, params={"min_count": min_count})


def top_genres_by_avg_score(engine: Engine, min_count: int = 30) -> pd.DataFrame:
    query = """
        SELECT g.name AS genre,
               COUNT(*) AS anime_count,
               ROUND(AVG(a.mean_score)::numeric, 3) AS avg_score
        FROM anime a
        JOIN anime_genres ag ON ag.mal_id = a.mal_id
        JOIN genres g ON g.genre_id = ag.genre_id
        WHERE a.mean_score IS NOT NULL
        GROUP BY g.name
        HAVING COUNT(*) >= %(min_count)s
        ORDER BY avg_score DESC
    """
    return pd.read_sql(query, engine, params={"min_count": min_count})


def studio_output_by_year(engine: Engine) -> pd.DataFrame:
    query = """
        SELECT s.name AS studio,
               a.start_season_year AS year,
               COUNT(DISTINCT a.mal_id) AS anime_count
        FROM anime a
        JOIN anime_studios ast ON ast.mal_id = a.mal_id
        JOIN studios s ON s.studio_id = ast.studio_id
        WHERE a.start_season_year IS NOT NULL
        GROUP BY s.name, a.start_season_year
        ORDER BY year, anime_count DESC
    """
    return pd.read_sql(query, engine)


def studio_score_profile(engine: Engine, min_count: int = 30) -> pd.DataFrame:
    query = """
        SELECT s.name AS studio,
               COUNT(DISTINCT a.mal_id) AS anime_count,
               COUNT(DISTINCT a.mal_id) FILTER (WHERE a.mean_score IS NOT NULL) AS scored_count,
               ROUND(AVG(a.mean_score)::numeric, 3) AS mean_score,
               ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY a.mean_score))::numeric, 3)
                   AS median_score,
               ROUND((SUM(a.mean_score * a.num_scoring_users)
                      / NULLIF(SUM(a.num_scoring_users), 0))::numeric, 3) AS weighted_score
        FROM studios s
        JOIN anime_studios ast ON ast.studio_id = s.studio_id
        JOIN anime a ON a.mal_id = ast.mal_id
        GROUP BY s.studio_id, s.name
        HAVING COUNT(a.mean_score) >= %(min_count)s
        ORDER BY anime_count DESC
    """
    return pd.read_sql(query, engine, params={"min_count": min_count})


def source_score_profile(engine: Engine, min_count: int = 100) -> pd.DataFrame:
    query = """
        SELECT source,
               COUNT(*) AS anime_count,
               COUNT(mean_score) AS scored_count,
               ROUND(AVG(mean_score)::numeric, 3) AS mean_score,
               ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mean_score))::numeric, 3)
                   AS median_score
        FROM anime
        WHERE source IS NOT NULL
        GROUP BY source
        HAVING COUNT(mean_score) >= %(min_count)s
        ORDER BY anime_count DESC
    """
    return pd.read_sql(query, engine, params={"min_count": min_count})


def rating_score_profile(engine: Engine, min_count: int = 30) -> pd.DataFrame:
    query = """
        SELECT rating,
               COUNT(*) AS anime_count,
               COUNT(mean_score) AS scored_count,
               ROUND(AVG(mean_score)::numeric, 3) AS mean_score,
               ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mean_score))::numeric, 3)
                   AS median_score
        FROM anime
        WHERE rating IS NOT NULL
        GROUP BY rating
        HAVING COUNT(mean_score) >= %(min_count)s
        ORDER BY anime_count DESC
    """
    return pd.read_sql(query, engine, params={"min_count": min_count})


def episode_band_score_profile(engine: Engine, min_count: int = 30) -> pd.DataFrame:
    query = """
        WITH anime_bands AS (
            SELECT media_type,
                   CASE
                       WHEN num_episodes = 1 THEN '1'
                       WHEN num_episodes BETWEEN 2 AND 12 THEN '2-12'
                       WHEN num_episodes BETWEEN 13 AND 26 THEN '13-26'
                       WHEN num_episodes BETWEEN 27 AND 52 THEN '27-52'
                       WHEN num_episodes > 52 THEN '53+'
                   END AS episode_band,
                   mean_score
            FROM anime
            WHERE num_episodes > 0 AND media_type IS NOT NULL
        )
        SELECT media_type,
               episode_band,
               COUNT(*) AS anime_count,
               COUNT(mean_score) AS scored_count,
               ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mean_score))::numeric, 3)
                   AS median_score
        FROM anime_bands
        GROUP BY media_type, episode_band
        HAVING COUNT(mean_score) >= %(min_count)s
        ORDER BY media_type,
                 CASE episode_band WHEN '1' THEN 1 WHEN '2-12' THEN 2
                      WHEN '13-26' THEN 3 WHEN '27-52' THEN 4 ELSE 5 END
    """
    return pd.read_sql(query, engine, params={"min_count": min_count})


def audience_score_sample(engine: Engine, limit: int = 5000) -> pd.DataFrame:
    query = """
        SELECT mal_id, title, media_type, mean_score,
               num_list_users, num_scoring_users, popularity, rank
        FROM anime
        WHERE mean_score IS NOT NULL AND num_list_users > 0
        ORDER BY md5(mal_id::text)
        LIMIT %(limit)s
    """
    return pd.read_sql(query, engine, params={"limit": limit})


def score_distribution(engine: Engine) -> pd.DataFrame:
    query = "SELECT mean_score FROM anime WHERE mean_score IS NOT NULL"
    return pd.read_sql(query, engine)


def episodes_vs_score(engine: Engine) -> pd.DataFrame:
    query = """
        SELECT num_episodes, mean_score
        FROM anime
        WHERE num_episodes IS NOT NULL AND mean_score IS NOT NULL
    """
    return pd.read_sql(query, engine)


def top_ranked_anime(
    engine: Engine, min_scoring_users: int = 1000, limit: int = 25
) -> pd.DataFrame:
    query = """
        SELECT title, media_type, mean_score, rank, popularity, num_scoring_users
        FROM anime
        WHERE rank IS NOT NULL
          AND mean_score IS NOT NULL
          AND num_scoring_users >= %(min_scoring_users)s
        ORDER BY rank ASC
        LIMIT %(limit)s
    """
    return pd.read_sql(
        query,
        engine,
        params={"min_scoring_users": min_scoring_users, "limit": limit},
    )
