# Google Trends "trending now" from SerpAPI, every pull kept as a snapshot
import time

import pandas as pd
import serpapi

from . import config


def get_trending_searches(run_time):
    client = serpapi.Client(api_key=config.SERPAPI_KEY)
    params = {
        "engine": "google_trends_trending_now",
        "geo": config.GEO,
        "hours": config.TRENDS_HOURS,
    }

    # one retry after a pause, then fail so the run shows as failed
    results = None
    for attempt in range(2):
        try:
            results = client.search(params)
            break
        except Exception as e:
            print(f"SerpAPI attempt {attempt + 1} failed: {type(e).__name__}: {e}")
            time.sleep(10)
    if results is None:
        raise RuntimeError("SerpAPI search failed after 2 tries")

    rows = []
    for t in results.get("trending_searches", []):
        end_ts = t.get("end_timestamp")
        rows.append({
            "query": t["query"],
            "start_date": int(t["start_timestamp"]),
            "end_date": int(end_ts) if end_ts else None,   # empty = still going
            "active": t.get("active", False),
            "search_volume": t.get("search_volume"),
            "increase_percentage": t.get("increase_percentage"),
            "categories": ", ".join(c["name"] for c in t.get("categories", [])),
            "trend_breakdown": ", ".join(t.get("trend_breakdown", [])),
            "observed_at": run_time,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # unix seconds to UTC timestamps (a missing end stays empty)
    df["start_date"] = pd.to_datetime(df["start_date"], unit="s", utc=True)
    df["end_date"] = pd.to_datetime(df["end_date"], unit="s", utc=True)
    df["search_volume"] = df["search_volume"].astype("Int64")
    df["increase_percentage"] = df["increase_percentage"].astype("Int64")
    return df