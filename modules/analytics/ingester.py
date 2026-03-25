"""
Analytics Ingester — fetches YouTube Analytics data for all live videos
and stores daily snapshots in performance_snapshots.
"""

from datetime import date, timedelta

from googleapiclient.discovery import build
from loguru import logger

from db.connection import execute, fetchall
from modules.publish.uploader import get_youtube_service


class AnalyticsIngester:
    def __init__(self):
        creds_service = get_youtube_service()
        # Analytics API uses separate service
        from google.oauth2.credentials import Credentials
        from pathlib import Path
        from config.settings import settings
        creds = Credentials.from_authorized_user_file(settings.youtube_token_path)
        self.analytics = build("youtubeAnalytics", "v2", credentials=creds)
        self.youtube = creds_service

    def run(self, days_back: int = 1) -> int:
        """
        Ingest analytics for all live videos.
        `days_back`: how many days of history to fetch (default = yesterday).
        Returns count of snapshots saved.
        """
        live_videos = fetchall(
            """
            SELECT pq.id as queue_id, pq.youtube_video_id, pq.uploaded_at
            FROM publish_queue pq
            WHERE pq.upload_status = 'live' AND pq.youtube_video_id IS NOT NULL
            """
        )

        if not live_videos:
            logger.info("No live videos to ingest analytics for.")
            return 0

        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=days_back - 1)

        saved = 0
        for video in live_videos:
            try:
                count = self._ingest_video(
                    queue_id=video["queue_id"],
                    video_id=video["youtube_video_id"],
                    start_date=start_date,
                    end_date=end_date,
                )
                saved += count
            except Exception as e:
                logger.warning(f"Failed to ingest analytics for {video['youtube_video_id']}: {e}")

        logger.info(f"Ingested {saved} analytics snapshots.")
        return saved

    def _ingest_video(
        self,
        queue_id: int,
        video_id: str,
        start_date: date,
        end_date: date,
    ) -> int:
        response = self.analytics.reports().query(
            ids=f"channel==MINE",
            startDate=str(start_date),
            endDate=str(end_date),
            metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained",
            dimensions="day",
            filters=f"video=={video_id}",
        ).execute()

        rows = response.get("rows", [])
        saved = 0

        for row in rows:
            snapshot_date = row[0]  # YYYY-MM-DD
            (views, watch_min, avg_duration, avg_pct,
             likes, comments, shares, subs) = row[1:]

            # Compute composite performance score
            perf_score = self._compute_score(
                views=int(views),
                avg_view_pct=float(avg_pct),
                likes=int(likes),
                comments=int(comments),
            )

            try:
                execute(
                    """
                    INSERT OR REPLACE INTO performance_snapshots
                        (publish_queue_id, youtube_video_id, snapshot_date,
                         views, watch_time_minutes, avg_view_duration, avg_view_pct,
                         likes, comments, shares, subscribers_gained, performance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        queue_id, video_id, snapshot_date,
                        int(views), float(watch_min), float(avg_duration), float(avg_pct),
                        int(likes), int(comments), int(shares), int(subs),
                        perf_score,
                    ),
                )
                saved += 1
            except Exception as e:
                logger.warning(f"Failed to save snapshot for {video_id} on {snapshot_date}: {e}")

        return saved

    def _compute_score(
        self,
        views: int,
        avg_view_pct: float,
        likes: int,
        comments: int,
    ) -> float:
        """
        Composite performance score (0.0–1.0).

        Weights:
          - View count (normalized vs channel median): 40%
          - Average view % (retention): 35%
          - Engagement rate (likes + comments / views): 25%
        """
        # Get channel median views for normalization
        median_row = fetchall(
            """
            SELECT AVG(views) as median_views
            FROM (
                SELECT views FROM performance_snapshots
                ORDER BY views LIMIT 50
            )
            """
        )
        median_views = median_row[0]["median_views"] if median_row and median_row[0]["median_views"] else 1000

        view_score = min(views / (median_views * 3), 1.0)
        retention_score = min(avg_view_pct / 100.0, 1.0)
        engagement_rate = (likes + comments) / max(views, 1)
        engagement_score = min(engagement_rate / 0.05, 1.0)  # 5% = perfect

        return round(
            0.40 * view_score + 0.35 * retention_score + 0.25 * engagement_score,
            4,
        )
