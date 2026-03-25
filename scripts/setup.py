"""
Setup script — initializes the database, creates directories, validates config.

Run once before first use:
    python scripts/setup.py
"""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


def setup():
    logger.info("Setting up YouTube Shorts OS...")

    # 1. Create required directories
    dirs = [
        "data",
        "data/assets/audio",
        "data/assets/music/dark_ambient",
        "data/assets/music/tense",
        "data/assets/music/calm",
        "data/assets/broll",
        "output",
        "logs",
        "config",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info(f"Created {len(dirs)} directories.")

    # 2. Check .env exists
    if not Path(".env").exists():
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            logger.warning(".env created from .env.example — fill in your API keys before running.")
        else:
            logger.error(".env.example not found. Cannot create .env.")
            sys.exit(1)

    # 3. Validate settings load
    try:
        from config.settings import settings
        logger.info(f"Config loaded. Database: {settings.database_path}")
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        logger.error("Make sure all required values are set in .env")
        sys.exit(1)

    # 4. Initialize database
    try:
        from db.connection import initialize_db
        initialize_db()
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

    # 5. Check FFmpeg is available (via bundled imageio_ffmpeg or system PATH)
    import subprocess
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        result = subprocess.run([ffmpeg_exe, "-version"], capture_output=True, timeout=5)
        if result.returncode == 0:
            logger.info(f"FFmpeg found (bundled): {ffmpeg_exe}")
        else:
            logger.warning("Bundled FFmpeg returned non-zero.")
    except Exception:
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            logger.info("FFmpeg found (system PATH).")
        except FileNotFoundError:
            logger.warning("FFmpeg not found. Install FFmpeg or ensure imageio_ffmpeg is installed.")

    # 6. Print next steps
    print("\n" + "="*60)
    print("Setup complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Fill in API keys in .env")
    print("  2. Set up YouTube OAuth:")
    print("     - Go to Google Cloud Console")
    print("     - Enable YouTube Data API v3 + YouTube Analytics API")
    print("     - Download OAuth2 client_secrets.json -> config/client_secrets.json")
    print("  3. Add background music to data/assets/music/")
    print("  4. Start the dashboard:")
    print("     streamlit run modules/dashboard/app.py")
    print("  5. Run first research pass:")
    print("     python scripts/run_pipeline.py research")
    print("  6. Run first production pass:")
    print("     python scripts/run_pipeline.py produce")
    print()


if __name__ == "__main__":
    setup()
