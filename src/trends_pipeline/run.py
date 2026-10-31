# The pipeline: for each source, fetch, save the raw file, add to the lakehouse
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import config, lake, storage
from .search import get_trending_searches
from .youtube import get_youtube_trending

# source name (also the table name) and the function that fetches it
SOURCES = {
    "trending_searches": get_trending_searches,
    "youtube_trending": get_youtube_trending,
}


def run_source(name, fetch, run_time):
    df = fetch(run_time)
    if df.empty:
        print(f"{name}: nothing returned, skipping")
        return
    print(f"{name}: got {len(df)} rows")

    # raw layer: one parquet file per source per run, in date folders
    file_name = f"{name}_{run_time:%Y%m%dT%H%M%SZ}.parquet"
    key = (
        f"raw/searches/{name}/year={run_time:%Y}/month={run_time:%m}/"
        f"day={run_time:%d}/{file_name}"
    )

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / file_name
        df.to_parquet(path, index=False)
        storage.upload(path, key)
        print(f"{name}: uploaded {key}")
        lake.load(name, path)


def main():
    run_time = datetime.now(timezone.utc)
    print(f"trends window: {config.TRENDS_HOURS} hours")

    failed = []
    for name, fetch in SOURCES.items():
        try:
            run_source(name, fetch, run_time)
        except Exception as e:
            print(f"{name}: FAILED ({type(e).__name__}: {e})")
            failed.append(name)

    # one source failing doesn't stop the other, but the run shows as failed
    if failed:
        raise SystemExit(f"Failed sources: {', '.join(failed)}")


if __name__ == "__main__":
    main()