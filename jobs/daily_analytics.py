"""
Daily Analytics Job — ingests performance data and runs analysis pass.
"""

from loguru import logger

from modules.analytics.ingester import AnalyticsIngester
from modules.analytics.analyzer import PerformanceAnalyzer


def run_daily_analytics() -> dict:
    logger.info("=== Daily Analytics Run Starting ===")

    ingester = AnalyticsIngester()
    snapshots = ingester.run(days_back=1)

    analyzer = PerformanceAnalyzer()
    analysis = analyzer.run()

    report = {
        "snapshots_ingested": snapshots,
        "patterns_updated": analysis.get("pattern_updates", 0),
        "insights_generated": analysis.get("insights_generated", 0),
    }

    logger.info(f"=== Analytics Complete: {report} ===")
    return report
