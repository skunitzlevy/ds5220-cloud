import json
import logging
import os
import textwrap
import time
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import boto3
import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import requests
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Add or remove YouTube videos here.
VIDEO_URLS = [
    "https://www.youtube.com/watch?v=Qxsa7ZJsLLI",
    "https://www.youtube.com/watch?v=MZaIMc1r0Uo",
    "https://www.youtube.com/watch?v=Qnof3u6sJtQ",
]

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/videos"
DEFAULT_PLOT_KEY = "latest.png"
LOCAL_PLOT_PATH = "/tmp/youtube_view_counts.png"
EASTERN_TIME = ZoneInfo("America/New_York")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def load_local_env():
    """Load .env only during local development.

    AWS Lambda receives environment variables from the Lambda configuration, so
    this function quietly does nothing if python-dotenv is not available there.
    """
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return

    try:
        from dotenv import load_dotenv

        load_dotenv()
        logger.info("Loaded local .env file")
    except ImportError:
        logger.info("python-dotenv is not installed; skipping local .env loading")


def get_config():
    """Read required configuration from environment variables."""
    load_local_env()

    config = {
        "api_key": os.getenv("API_KEY"),
        "table_name": os.getenv("TABLE_NAME"),
        "bucket_name": os.getenv("BUCKET_NAME"),
        "plot_key": os.getenv("PLOT_KEY", DEFAULT_PLOT_KEY),
    }

    missing = [
        name
        for name, value in {
            "API_KEY": config["api_key"],
            "TABLE_NAME": config["table_name"],
            "BUCKET_NAME": config["bucket_name"],
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    return config


def extract_video_id(video_url):
    """Extract the YouTube video id from common YouTube URL shapes."""
    parsed = urlparse(video_url)
    host = parsed.netloc.lower()

    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        query = parse_qs(parsed.query)
        video_id = query.get("v", [""])[0]
    else:
        video_id = ""

    if not video_id:
        raise ValueError(f"Could not extract video id from URL: {video_url}")

    return video_id


def build_video_lookup(video_urls):
    """Return a mapping from video_id to original URL."""
    lookup = {}
    for video_url in video_urls:
        try:
            video_id = extract_video_id(video_url)
            lookup[video_id] = video_url
            logger.info("Tracking video_id=%s url=%s", video_id, video_url)
        except ValueError:
            logger.exception("Skipping invalid YouTube URL: %s", video_url)
    return lookup


def fetch_youtube_videos(api_key, video_ids):
    """Fetch snippet and statistics for the configured videos."""
    if not video_ids:
        logger.warning("No valid video ids were configured")
        return []

    params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids),
        "key": api_key,
    }

    try:
        logger.info("Fetching YouTube data for %d videos", len(video_ids))
        response = requests.get(YOUTUBE_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        logger.exception("YouTube API request failed")
        raise
    except ValueError:
        logger.exception("YouTube API returned invalid JSON")
        raise

    items = data.get("items", [])
    returned_ids = {item.get("id") for item in items}
    missing_ids = sorted(set(video_ids) - returned_ids)
    if missing_ids:
        logger.warning("YouTube did not return data for video ids: %s", missing_ids)

    logger.info("Fetched data for %d videos", len(items))
    return items


def make_dynamodb_item(youtube_item, video_url, timestamp):
    """Convert one YouTube API item into the DynamoDB record shape."""
    snippet = youtube_item.get("snippet", {})
    statistics = youtube_item.get("statistics", {})

    return {
        "video_id": youtube_item["id"],
        "timestamp": timestamp,
        "title": snippet.get("title", "Untitled video"),
        "channel": snippet.get("channelTitle", "Unknown channel"),
        "published_at": snippet.get("publishedAt", ""),
        "view_count": int(statistics.get("viewCount", 0)),
        "video_url": video_url,
    }


def write_records(table, youtube_items, video_lookup, timestamp):
    """Write one timestamped DynamoDB record for each video."""
    written = []

    for youtube_item in youtube_items:
        try:
            video_id = youtube_item["id"]
            item = make_dynamodb_item(
                youtube_item=youtube_item,
                video_url=video_lookup.get(video_id, ""),
                timestamp=timestamp,
            )
            table.put_item(Item=item)
            written.append(item)
            logger.info(
                "Wrote DynamoDB record video_id=%s timestamp=%s view_count=%s",
                item["video_id"],
                item["timestamp"],
                item["view_count"],
            )
        except ClientError:
            logger.exception("DynamoDB put_item failed for item: %s", youtube_item)
        except (KeyError, TypeError, ValueError):
            logger.exception(
                "Could not build DynamoDB record from item: %s", youtube_item
            )

    return written


def query_video_history(table, video_id):
    """Read the full timestamp-ordered history for one video."""
    try:
        response = table.query(
            KeyConditionExpression=Key("video_id").eq(video_id),
            ScanIndexForward=True,
        )
        items = response.get("Items", [])

        while "LastEvaluatedKey" in response:
            response = table.query(
                KeyConditionExpression=Key("video_id").eq(video_id),
                ExclusiveStartKey=response["LastEvaluatedKey"],
                ScanIndexForward=True,
            )
            items.extend(response.get("Items", []))

        logger.info("Loaded %d history records for video_id=%s", len(items), video_id)
        return items
    except ClientError:
        logger.exception("DynamoDB query failed for video_id=%s", video_id)
        return []


def decimal_to_int(value):
    """DynamoDB may return numbers as Decimal; matplotlib wants plain numbers."""
    if isinstance(value, Decimal):
        return int(value)
    return int(value)


def clean_video_title(title, fallback):
    """Shorten YouTube titles for readable plot legends.

    NBA highlight titles often look like:
    "#7 76ERS at #2 CELTICS | FULL GAME 5 HIGHLIGHTS | April 28, 2026"

    For the legend, the matchup before the first "|" is usually the clearest
    label, so this returns "#7 76ERS at #2 CELTICS".
    """
    cleaned_title = (title or fallback).split("|", 1)[0].strip()
    if not cleaned_title:
        cleaned_title = fallback

    return textwrap.fill(cleaned_title, width=32)


def generate_plot(history_by_video, output_path):
    """Generate a line chart of view counts over time."""
    if not any(history_by_video.values()):
        raise ValueError("No DynamoDB history available to plot")

    fig, ax = plt.subplots(figsize=(12, 7))

    for video_id, items in history_by_video.items():
        if not items:
            logger.warning("No history to plot for video_id=%s", video_id)
            continue

        times = [
            datetime.fromtimestamp(
                decimal_to_int(item["timestamp"]), tz=timezone.utc
            ).astimezone(EASTERN_TIME)
            for item in items
        ]
        view_counts = [decimal_to_int(item["view_count"]) for item in items]
        legend_title = clean_video_title(items[-1].get("title"), video_id)

        ax.plot(times, view_counts, marker="o", linewidth=2, label=legend_title)

    ax.set_title("NBA YouTube Highlight Views Over Time")
    ax.set_xlabel("Time Tracked (Eastern)")
    ax.set_ylabel("View Count")
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(lambda value, position: f"{int(value):,}")
    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%m/%d %H:%M", tz=EASTERN_TIME)
    )

    for label in ax.get_xticklabels():
        label.set_rotation(30)
        label.set_horizontalalignment("right")

    ax.legend(
        title="Video",
        fontsize=8,
        title_fontsize=9,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.22),
        ncol=1,
        frameon=True,
    )
    fig.tight_layout()

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, format="png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("Saved plot to %s", output_file)

    return str(output_file)


def upload_plot_to_s3(s3_client, bucket_name, plot_key, local_path):
    """Upload the generated plot to S3.

    Public read access should be handled by the bucket policy, not by an object
    ACL. Modern S3 buckets often use "bucket owner enforced" Object Ownership,
    which disables ACLs entirely.
    """
    content_type = "image/png"
    public_url = f"https://{bucket_name}.s3.amazonaws.com/{plot_key}"

    try:
        s3_client.upload_file(
            local_path,
            bucket_name,
            plot_key,
            ExtraArgs={"ContentType": content_type},
        )
        logger.info("Uploaded plot to %s", public_url)
        return {"url": public_url}
    except ClientError:
        logger.exception("S3 plot upload failed")
        raise


def run_ingestion():
    """Run the whole ingestion flow once."""
    config = get_config()
    video_lookup = build_video_lookup(VIDEO_URLS)
    video_ids = list(video_lookup.keys())
    timestamp = int(time.time())

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(config["table_name"])
    s3_client = boto3.client("s3")

    youtube_items = fetch_youtube_videos(config["api_key"], video_ids)
    written_records = write_records(table, youtube_items, video_lookup, timestamp)

    history_by_video = defaultdict(list)
    for video_id in video_ids:
        history_by_video[video_id] = query_video_history(table, video_id)

    local_plot_path = generate_plot(history_by_video, LOCAL_PLOT_PATH)
    plot_upload = upload_plot_to_s3(
        s3_client=s3_client,
        bucket_name=config["bucket_name"],
        plot_key=config["plot_key"],
        local_path=local_plot_path,
    )

    return {
        "ok": True,
        "timestamp": timestamp,
        "videos_configured": len(video_ids),
        "records_written": len(written_records),
        "plot_url": plot_upload["url"],
    }


def lambda_handler(event, context):
    """AWS Lambda entry point."""
    try:
        result = run_ingestion()
        return {
            "statusCode": 200,
            "body": json.dumps(result),
        }
    except Exception as error:
        logger.exception("Ingestion failed")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "ok": False,
                    "error": str(error),
                }
            ),
        }


if __name__ == "__main__":
    response = lambda_handler(event={}, context=None)
    print(json.dumps(response, indent=2))
