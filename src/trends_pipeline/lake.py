# The searches lakehouse: own catalog schema and own folder in the shared bucket
from pathlib import Path

import duckdb

from . import config

TABLES = {
    "trending_searches": """
        CREATE TABLE IF NOT EXISTS lake.trending_searches (
            query VARCHAR,
            start_date TIMESTAMPTZ,
            end_date TIMESTAMPTZ,
            active BOOLEAN,
            search_volume BIGINT,
            increase_percentage BIGINT,
            categories VARCHAR,
            trend_breakdown VARCHAR,
            observed_at TIMESTAMPTZ,
            source_file VARCHAR
        )
    """,
    "youtube_trending": """
        CREATE TABLE IF NOT EXISTS lake.youtube_trending (
            region_code VARCHAR,
            chart_rank BIGINT,
            video_id VARCHAR,
            title VARCHAR,
            channel_title VARCHAR,
            category_id VARCHAR,
            category_name VARCHAR,
            published_at TIMESTAMPTZ,
            tags VARCHAR,
            duration_secs BIGINT,
            view_count BIGINT,
            like_count BIGINT,
            comment_count BIGINT,
            observed_at TIMESTAMPTZ,
            source_file VARCHAR
        )
    """,
}


def connect():
    # Open DuckDB with the bucket credentials and attach the lakehouse
    host = config.B2_ENDPOINT.replace("https://", "")
    region = host.split(".")[1]            # e.g. us-west-004

    con = duckdb.connect()
    for extension in ("ducklake", "postgres"):
        con.execute(f"INSTALL {extension}")
        con.execute(f"LOAD {extension}")
    con.execute(f"""
        CREATE OR REPLACE SECRET b2 (
            TYPE s3,
            KEY_ID '{config.B2_KEY_ID}',
            SECRET '{config.B2_APP_KEY}',
            ENDPOINT '{host}',
            REGION '{region}',
            URL_STYLE 'path'
        )
    """)
    con.execute(f"""
        ATTACH 'ducklake:postgres:{config.PG_CATALOG}' AS lake (
            DATA_PATH 's3://{config.B2_BUCKET}/lake/searches/',
            METADATA_SCHEMA 'searches',
            DATA_INLINING_ROW_LIMIT 0
        )
    """)
    return con


def load(table, parquet_path):
    # Add one raw parquet file to a table, skipping files already loaded
    name = Path(parquet_path).name
    con = connect()
    con.execute(TABLES[table])

    already = con.execute(
        f"SELECT COUNT(*) FROM lake.{table} WHERE source_file = ?", [name]
    ).fetchone()[0]
    if already:
        print(f"already loaded, skipping {name}")
    else:
        con.execute(f"""
            INSERT INTO lake.{table} BY NAME
            SELECT *, '{name}' AS source_file
            FROM read_parquet('{Path(parquet_path).as_posix()}')
        """)
        print(f"loaded {name} into the lakehouse")

    con.execute("DETACH lake")
    con.close()