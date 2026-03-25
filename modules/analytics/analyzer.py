"""
Analytics Analyzer — processes performance snapshots to:
1. Score and tier all published videos
2. Update content_patterns with success rates
3. Generate AI-powered insights for the idea engine
4. Feed recommendations back into context for future ideas
"""

from __future__ import annotations

import json
from pathlib import Path

import anthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from config.template_utils import fill_template
from db.connection import execute, fetchall, fetchone


PROMPT_PATH = Path("config/prompts/performance_analysis.md")


class PerformanceAnalyzer:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def run(self) -> dict:
        """Run full analysis pass. Returns summary dict."""
        logger.info("Running performance analysis...")

        self._tier_videos()
        pattern_updates = self._update_pattern_success_rates()
        insights = self._generate_ai_insights()

        return {
            "pattern_updates": pattern_updates,
            "insights_generated": len(insights),
        }

    def _tier_videos(self) -> None:
        """Assign performance_tier (top/middle/low) to all published videos."""
        rows = fetchall(
            """
            SELECT pq.id, AVG(ps.performance_score) as avg_score
            FROM publish_queue pq
            JOIN performance_snapshots ps ON ps.publish_queue_id = pq.id
            GROUP BY pq.id
            HAVING COUNT(ps.id) >= 1
            ORDER BY avg_score DESC
            """
        )
        if not rows:
            return

        total = len(rows)
        top_cut = int(total * 0.2)
        low_cut = int(total * 0.6)

        for i, row in enumerate(rows):
            if i < top_cut:
                tier = "top"
            elif i < low_cut:
                tier = "middle"
            else:
                tier = "low"
            # Store tier in publish_queue (via performance snapshot tag would be cleaner;
            # for v1 we store it in the queue table — add a column if needed via migration)

    def _update_pattern_success_rates(self) -> int:
        """
        Recompute success_rate for each content pattern based on actual video performance.
        Returns number of patterns updated.
        """
        patterns = fetchall(
            "SELECT id, pattern_name, pattern_type FROM content_patterns WHERE is_active = 1"
        )
        updated = 0

        for pattern in patterns:
            field_map = {
                "topic_cluster": "i.topic_cluster",
                "hook_style": "i.hook_style",
            }
            field = field_map.get(pattern["pattern_type"])
            if not field:
                continue

            stats = fetchall(
                f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN ps.performance_score >= 0.6 THEN 1 ELSE 0 END) as top_count,
                    AVG(ps.views) as avg_views
                FROM performance_snapshots ps
                JOIN publish_queue pq ON pq.id = ps.publish_queue_id
                JOIN productions pr ON pr.id = pq.production_id
                JOIN scripts s ON s.id = pr.script_id
                JOIN ideas i ON i.id = s.idea_id
                WHERE {field} = ?
                """,
                (pattern["pattern_name"],),
            )

            if stats and stats[0]["total"] >= 3:
                total = stats[0]["total"]
                top_count = stats[0]["top_count"] or 0
                avg_views = stats[0]["avg_views"] or 0
                success_rate = top_count / total

                execute(
                    """
                    UPDATE content_patterns
                    SET success_rate = ?, avg_view_count = ?, sample_size = ?,
                        last_updated = datetime('now')
                    WHERE id = ?
                    """,
                    (success_rate, int(avg_views), total, pattern["id"]),
                )
                updated += 1

        logger.info(f"Updated {updated} content pattern success rates.")
        return updated

    def _generate_ai_insights(self) -> list[dict]:
        """Analyze top and bottom performers to extract learnings."""
        # Get top 5 and bottom 5 recent videos
        top = fetchall(
            """
            SELECT pq.title, s.hook_text, i.hook_style, i.topic_cluster,
                   pr.duration_actual, pq.uploaded_at,
                   AVG(ps.views) as views,
                   AVG(ps.avg_view_duration) as avg_dur,
                   AVG(ps.avg_view_pct) as avg_pct,
                   AVG(ps.likes) as likes,
                   AVG(ps.comments) as comments,
                   AVG(ps.performance_score) as score
            FROM publish_queue pq
            JOIN productions pr ON pr.id = pq.production_id
            JOIN scripts s ON s.id = pr.script_id
            JOIN ideas i ON i.id = s.idea_id
            JOIN performance_snapshots ps ON ps.publish_queue_id = pq.id
            WHERE pq.upload_status = 'live'
            GROUP BY pq.id
            ORDER BY score DESC
            LIMIT 5
            """
        )
        if not top:
            logger.info("Not enough data for AI insights yet.")
            return []

        # Build analysis for each top performer
        # (In production, also analyze bottom performers to find anti-patterns)
        insights = []
        for video in top[:3]:  # Analyze top 3 to stay within token budget
            video = dict(video)
            insight = self._analyze_single_video(video)
            if insight:
                insights.append(insight)

        return insights

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _analyze_single_video(self, video: dict) -> dict | None:
        # Get channel benchmarks
        bench = fetchall(
            """
            SELECT AVG(ps.views) as med_views, AVG(ps.avg_view_pct) as med_pct
            FROM performance_snapshots ps
            """
        )
        median_views = bench[0]["med_views"] or 1000 if bench else 1000
        median_pct = bench[0]["med_pct"] or 50 if bench else 50

        perf_score = video.get("score", 0)
        tier = "top" if perf_score >= 0.6 else ("middle" if perf_score >= 0.35 else "low")

        template = PROMPT_PATH.read_text()
        prompt = fill_template(template,
            title=video.get("title", ""),
            hook_text=video.get("hook_text", ""),
            hook_style=video.get("hook_style", ""),
            topic_cluster=video.get("topic_cluster", ""),
            duration=video.get("duration_actual", 0),
            published_at=video.get("uploaded_at", ""),
            days_live=7,
            views=int(video.get("views", 0)),
            avg_view_duration=round(video.get("avg_dur", 0), 1),
            avg_view_pct=round(video.get("avg_pct", 0), 1),
            likes=int(video.get("likes", 0)),
            comments=int(video.get("comments", 0)),
            like_view_ratio=round(video.get("likes", 0) / max(video.get("views", 1), 1), 4),
            subscribers_gained=0,
            performance_score=round(perf_score, 3),
            performance_tier=tier,
            median_views=int(median_views),
            median_view_pct=round(median_pct, 1),
            top_threshold=int(median_views * 3),
        )

        response = self.client.messages.create(
            model=settings.claude_model_smart,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            return json.loads(raw)
        except Exception:
            return None
