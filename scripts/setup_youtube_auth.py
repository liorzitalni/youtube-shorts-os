"""
YouTube OAuth2 Setup — runs the browser-based auth flow once to create
youtube_token.json. Run this once before using the upload or analytics features.

Usage:
    python scripts/setup_youtube_auth.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


def setup_auth():
    secrets_path = Path("config/client_secrets.json")
    if not secrets_path.exists():
        print("\nERROR: config/client_secrets.json not found.")
        print()
        print("Steps to get it:")
        print("  1. Go to https://console.cloud.google.com")
        print("  2. Create or select a project")
        print("  3. Enable APIs:")
        print("     - YouTube Data API v3")
        print("     - YouTube Analytics API v2")
        print("  4. Go to: APIs & Services > Credentials")
        print("  5. Create credentials > OAuth 2.0 Client ID")
        print("  6. Application type: Desktop app")
        print("  7. Download JSON > save to: config/client_secrets.json")
        print("  8. Re-run this script")
        sys.exit(1)

    logger.info("Starting YouTube OAuth2 flow...")
    logger.info("A browser window will open. Sign in and grant access.")

    try:
        from modules.publish.uploader import get_youtube_service
        service = get_youtube_service()

        # Verify it works
        result = service.channels().list(part="snippet", mine=True).execute()
        items = result.get("items", [])
        if items:
            channel = items[0]["snippet"]
            logger.info(f"Authenticated as: {channel['title']}")
        else:
            logger.warning("Authenticated but no channel found on this account.")

        token_path = Path("config/youtube_token.json")
        logger.info(f"Token saved to: {token_path}")
        print("\nYouTube auth complete. You can now upload videos.")

    except Exception as e:
        logger.error(f"Auth failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_auth()
