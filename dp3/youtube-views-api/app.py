import logging
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from chalice import Chalice

app = Chalice(app_name="youtube-views-api")

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
PLOT_KEY = os.environ.get("PLOT_KEY", "latest.png")
ONE_HOUR_SECONDS = 60 * 60

VIDEO_IDS = [
    "Qxsa7ZJsLLI",
    "MZaIMc1r0Uo",
    "Qnof3u6sJtQ",
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def decimal_to_int(value):
    if isinstance(value, Decimal):
        return int(value)
    return value


def clean_title(title, fallback):
    return (title or fallback).split("|", 1)[0].strip() or fallback


def make_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")

    return "\n".join(lines)


def get_latest_record(video_id):
    try:
        response = table.query(
            KeyConditionExpression=Key("video_id").eq(video_id),
            ScanIndexForward=False,
            Limit=1,
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError:
        logger.exception("Failed to load latest record for video_id=%s", video_id)
        return None


def get_record_at_or_before(video_id, timestamp):
    try:
        response = table.query(
            KeyConditionExpression=(
                Key("video_id").eq(video_id) & Key("timestamp").lte(timestamp)
            ),
            ScanIndexForward=False,
            Limit=1,
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError:
        logger.exception(
            "Failed to load comparison record for video_id=%s timestamp=%s",
            video_id,
            timestamp,
        )
        return None


@app.route("/")
def index():
    return {
        "about": "Tracks YouTube view counts over time for several NBA highlight videos.",
        "resources": ["current", "trend", "plot"],
    }


@app.route("/current")
def current():
    rows = []

    for video_id in VIDEO_IDS:
        record = get_latest_record(video_id)

        if not record:
            rows.append([video_id, "no data yet"])
            continue

        title = clean_title(record.get("title"), video_id)
        view_count = decimal_to_int(record.get("view_count", 0))

        rows.append([title, f"{view_count:,}"])

    return {"response": make_table(["Video", "Latest views"], rows)}


@app.route("/trend")
def trend():
    rows = []

    for video_id in VIDEO_IDS:
        latest = get_latest_record(video_id)

        if not latest:
            rows.append([video_id, "no data yet", "-", "-"])
            continue

        latest_timestamp = decimal_to_int(latest.get("timestamp", 0))
        one_hour_ago = latest_timestamp - ONE_HOUR_SECONDS
        comparison = get_record_at_or_before(video_id, one_hour_ago)
        title = clean_title(latest.get("title"), video_id)

        if not comparison:
            rows.append([title, "not enough data", "-", "-"])
            continue

        comparison_views = decimal_to_int(comparison.get("view_count", 0))
        latest_views = decimal_to_int(latest.get("view_count", 0))

        if comparison_views == 0:
            rows.append([title, f"{latest_views:,}", "0", "cannot calculate"])
            continue

        percent_change = ((latest_views - comparison_views) / comparison_views) * 100

        rows.append(
            [
                title,
                f"{latest_views:,}",
                f"{comparison_views:,}",
                f"{percent_change:+.2f}%",
            ]
        )

    return {
        "response": make_table(
            ["Video", "Latest views", "Views 1 hour ago", "% change (1 hour)"],
            rows,
        )
    }


@app.route("/plot")
def plot():
    plot_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{PLOT_KEY}"
    return {"response": plot_url}
