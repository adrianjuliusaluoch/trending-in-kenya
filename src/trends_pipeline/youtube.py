# YouTube "most popular" chart (top 25), every pull kept as a snapshot
import json

import isodate
import pandas as pd
from googleapiclient.discovery import build

from . import config


def to_seconds(duration):
    # ISO 8601 duration like PT4M13S to seconds
    try:
        return int(isodate.parse_duration(duration).total_seconds())
    except Exception:
        return None


def to_int(value):
    # hidden likes or comments stay empty instead of becoming 0
    return int(value) if value is not None else None


def get_youtube_trending(run_time):
    youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)

    # category id to name
    categories = youtube.videoCategories().list(
        part="snippet", regionCode=config.YOUTUBE_REGION
    ).execute()
    category_map = {
        c["id"]: c["snippet"]["title"] for c in categories.get("items", [])
    }

    # one request is enough for the top 25
    response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        chart="mostPopular",
        regionCode=config.YOUTUBE_REGION,
        maxResults=config.YOUTUBE_TOP,
    ).execute()

    rows = []
    for rank, item in enumerate(response.get("items", []), start=1):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        category_id = snippet.get("categoryId")
        rows.append({
            "region_code": config.YOUTUBE_REGION,
            "chart_rank": rank,
            "video_id": item.get("id"),
            "title": snippet.get("title"),
            "channel_title": snippet.get("channelTitle"),
            "category_id": category_id,
            "category_name": category_map.get(category_id, "Unknown"),
            "published_at": snippet.get("publishedAt"),
            "tags": json.dumps(snippet.get("tags", [])),
            "duration_secs": to_seconds(
                item.get("contentDetails", {}).get("duration")
            ),
            "view_count": to_int(stats.get("viewCount")),
            "like_count": to_int(stats.get("likeCount")),
            "comment_count": to_int(stats.get("commentCount")),
            "observed_at": run_time,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["published_at"] = pd.to_datetime(df["published_at"], utc=True)
    int_columns = ["duration_secs", "view_count", "like_count", "comment_count"]
    df[int_columns] = df[int_columns].astype("Int64")
    return df