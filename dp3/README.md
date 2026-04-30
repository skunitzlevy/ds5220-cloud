# NBA YouTube Highlight View Tracker

This project tracks YouTube view counts for selected NBA playoff highlight videos over time. When Oklahoma City and Indiana played in the finals last year, there was some commentary about both teams being from relatively smaller metro areas. I was curious to track the view counts of the NBA playoff highlight videos on youtube to see if the high view counts roughly corresponded to the larger metropolitan areas.

## Data Collection and Storage

An AWS EventBridge rule runs the ingestion Lambda once per hour. Each run calls the YouTube Data API v3 for the configured video URLs, records the current view count for each video, writes the samples to DynamoDB, regenerates a line chart with matplotlib, and uploads the latest plot image to S3.

The DynamoDB table is `youtube-video-views`. It uses `video_id` as the string partition key and `timestamp` as the numeric sort key. Each stored record includes:

```text
video_id
timestamp
title
channel
published_at
view_count
video_url
```

The timestamp is stored as a Unix epoch integer, which makes it easy to query each video's history in time order and compare the latest sample against earlier samples.

## API Resources

The Chalice API exposes three resources:

`/current` returns a simple table with the latest tracked view count for each video in the configured video list.

`/trend` returns a simple table showing the percent change in views over the last 1 hour. It compares the latest sample for each video against the closest stored sample at or before one hour earlier, and the table labels the change as `% change (1 hour)`.

`/plot` returns the public S3 URL for the latest generated plot image. The plot shows view counts over time for the tracked videos.
