"""
API verification script — tests every external API connection.
Run this before first use and after any config change.

Usage:
    python scripts/verify_apis.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


def check(name: str, fn) -> bool:
    try:
        fn()
        logger.info(f"  [OK]  {name}")
        return True
    except Exception as e:
        logger.error(f"  [FAIL] {name}: {e}")
        return False


def verify_anthropic():
    from config.settings import settings
    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.claude_model_fast,
        max_tokens=10,
        messages=[{"role": "user", "content": "Reply with: OK"}],
    )
    assert response.content[0].text.strip(), "Empty response"


def verify_elevenlabs():
    from config.settings import settings
    if not settings.elevenlabs_api_key or settings.elevenlabs_api_key in ("...", ""):
        raise ValueError("ELEVENLABS_API_KEY not set in .env")
    from elevenlabs import ElevenLabs
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    voices = client.voices.get_all()
    assert voices, "No voices returned"


def verify_pexels():
    from config.settings import settings
    import httpx
    if not settings.pexels_api_key:
        raise ValueError("PEXELS_API_KEY not set in .env")
    resp = httpx.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": settings.pexels_api_key},
        params={"query": "brain", "per_page": 1},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    assert data.get("photos"), "No photos returned"


def verify_youtube():
    from config.settings import settings
    secrets_path = Path(settings.youtube_client_secrets_path)
    if not secrets_path.exists():
        raise FileNotFoundError(
            f"client_secrets.json not found at {secrets_path}\n"
            "Download from Google Cloud Console: APIs & Services > Credentials"
        )
    from modules.publish.uploader import get_youtube_service
    service = get_youtube_service()
    result = service.channels().list(part="id", mine=True).execute()
    assert result.get("items"), "No channel found for authenticated account"


def verify_database():
    from db.connection import fetchall
    tables = fetchall("SELECT name FROM sqlite_master WHERE type='table'")
    assert len(tables) >= 10, f"Expected 10+ tables, got {len(tables)}"


def verify_ffmpeg():
    import imageio_ffmpeg, subprocess
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run([exe, "-version"], capture_output=True, timeout=5)
    assert result.returncode == 0


if __name__ == "__main__":
    print("\n" + "="*50)
    print("YouTube Shorts OS — API Verification")
    print("="*50 + "\n")

    results = {
        "Database":    check("Database (SQLite)",          verify_database),
        "FFmpeg":      check("FFmpeg (bundled)",           verify_ffmpeg),
        "Anthropic":   check("Anthropic Claude API",       verify_anthropic),
        "ElevenLabs":  check("ElevenLabs TTS",             verify_elevenlabs),
        "Pexels":      check("Pexels B-roll API",          verify_pexels),
        "YouTube":     check("YouTube Data API (OAuth2)",  verify_youtube),
    }

    print()
    passed = sum(results.values())
    total = len(results)
    print(f"Result: {passed}/{total} checks passed")

    # Minimum viable set for first video (no YouTube upload yet)
    mvp = all([results["Database"], results["FFmpeg"], results["Anthropic"]])
    if mvp:
        print("\nMVP check PASSED — you can generate ideas, scripts, and render videos.")
        if not results["ElevenLabs"]:
            print("NOTE: ElevenLabs not configured — TTS will use synthetic fallback audio.")
        if not results["YouTube"]:
            print("NOTE: YouTube not configured — videos will be queued but not uploaded.")
    else:
        print("\nMVP check FAILED — fix the above errors before running the pipeline.")
        sys.exit(1)
