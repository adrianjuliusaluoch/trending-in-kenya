# Settings and secrets, all read from environment variables
import os

from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.environ["SERPAPI_KEY"]
YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
B2_ENDPOINT = os.environ["B2_ENDPOINT"]
B2_KEY_ID = os.environ["B2_KEY_ID"]
B2_APP_KEY = os.environ["B2_APP_KEY"]
B2_BUCKET = os.environ["B2_BUCKET"]
PG_CATALOG = os.environ["PG_CATALOG"]

# Where to look
GEO = "KE"
YOUTUBE_REGION = "KE"
YOUTUBE_TOP = 25          # how many top videos to keep each pull

# Trends window in hours: 24 for normal runs, 168 for a backfill
TRENDS_HOURS = int(os.environ.get("TRENDS_HOURS", "24"))
if TRENDS_HOURS not in (4, 24, 48, 168):
    raise ValueError("TRENDS_HOURS must be 4, 24, 48 or 168")