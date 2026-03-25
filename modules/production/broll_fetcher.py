"""
B-roll Fetcher — downloads stock footage from Pexels based on script visual_notes.
Downloads are cached locally to avoid re-fetching the same clips.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import httpx
from loguru import logger

from config.settings import settings
from db.connection import execute, fetchone


PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_URL = "https://api.pexels.com/v1/search"


class BrollFetcher:
    def __init__(self):
        self.api_key = settings.pexels_api_key
        self.cache_dir = Path(settings.assets_dir) / "broll"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {"Authorization": self.api_key}

    def fetch_for_production(self, production_id: int, queries: list[str]) -> list[str]:
        """
        Fetch B-roll clips for a production given a list of search queries.
        Returns list of local file paths. Updates productions.broll_paths.
        """
        if not self.api_key:
            logger.warning("PEXELS_API_KEY not set — skipping B-roll fetch.")
            return []

        paths = []
        for query in queries[:3]:  # cap at 3 clips to keep video manageable
            path = self._fetch_clip(query)
            if path:
                paths.append(path)

        if paths:
            execute(
                "UPDATE productions SET broll_paths = ? WHERE id = ?",
                (json.dumps(paths), production_id),
            )
            logger.info(f"Fetched {len(paths)} B-roll clips for production {production_id}.")

        return paths

    def _fetch_clip(self, query: str) -> str | None:
        """
        Fetch a single video clip matching the query.
        Returns local file path or None.
        """
        cache_key = hashlib.md5(query.encode()).hexdigest()[:10]
        cached = list(self.cache_dir.glob(f"{cache_key}_*.mp4"))
        if cached:
            logger.debug(f"B-roll cache hit for '{query}': {cached[0]}")
            return str(cached[0])

        try:
            resp = httpx.get(
                PEXELS_VIDEO_URL,
                headers=self.headers,
                params={
                    "query": query,
                    "per_page": 5,
                    "orientation": "portrait",   # 9:16 preferred
                    "size": "medium",
                },
                timeout=15,
            )
            resp.raise_for_status()
            videos = resp.json().get("videos", [])

            if not videos:
                logger.debug(f"No Pexels video results for '{query}'")
                return self._fetch_photo(query, cache_key)

            # Pick best portrait video
            video = self._pick_best_video(videos)
            if not video:
                return self._fetch_photo(query, cache_key)

            video_url = video["url"]
            filename = f"{cache_key}_{self._slugify(query)}.mp4"
            out_path = self.cache_dir / filename
            self._download(video_url, out_path)
            return str(out_path)

        except Exception as e:
            logger.warning(f"Failed to fetch B-roll for '{query}': {e}")
            return None

    def _fetch_photo(self, query: str, cache_key: str) -> str | None:
        """
        Fallback: fetch a still photo when no portrait video is available.
        Download as JPEG for use as a static frame in the video.
        """
        try:
            resp = httpx.get(
                PEXELS_PHOTO_URL,
                headers=self.headers,
                params={"query": query, "per_page": 3, "orientation": "portrait"},
                timeout=15,
            )
            resp.raise_for_status()
            photos = resp.json().get("photos", [])
            if not photos:
                return None

            photo_url = photos[0]["src"]["large"]
            filename = f"{cache_key}_{self._slugify(query)}.jpg"
            out_path = self.cache_dir / filename
            self._download(photo_url, out_path)
            return str(out_path)

        except Exception as e:
            logger.warning(f"Photo fallback failed for '{query}': {e}")
            return None

    def _pick_best_video(self, videos: list[dict]) -> dict | None:
        """Pick the best video file from results — prefer portrait HD."""
        for video in videos:
            files = video.get("video_files", [])
            # Prefer portrait files (height > width), HD resolution
            portrait = [
                f for f in files
                if f.get("width", 0) < f.get("height", 1)
                and f.get("width", 0) >= 720
                and f.get("file_type") == "video/mp4"
            ]
            if portrait:
                # Pick highest resolution portrait
                best = sorted(portrait, key=lambda f: f.get("width", 0), reverse=True)[0]
                return {"url": best["link"]}

            # Fallback: any MP4
            mp4_files = [f for f in files if f.get("file_type") == "video/mp4"]
            if mp4_files:
                return {"url": mp4_files[0]["link"]}

        return None

    def _download(self, url: str, path: Path) -> None:
        logger.debug(f"Downloading: {url} -> {path}")
        with httpx.stream("GET", url, timeout=60, follow_redirects=True) as resp:
            resp.raise_for_status()
            with open(path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=8192):
                    f.write(chunk)

    def _slugify(self, text: str) -> str:
        import re
        return re.sub(r"[^a-z0-9]+", "_", text.lower())[:30]


def extract_broll_queries(visual_notes: str) -> list[str]:
    """
    Extract 3 search queries from the visual_notes field of a script.
    Falls back to sensible psychology defaults.
    """
    if not visual_notes:
        return ["human brain dark background", "person thinking alone", "dark abstract"]

    import anthropic
    from config.settings import settings

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.claude_model_fast,
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": (
                f"Extract exactly 3 Pexels stock footage search queries from these visual notes. "
                f"Return ONLY a JSON array of 3 short strings (2-4 words each, no quotes inside).\n\n"
                f"Visual notes: {visual_notes}"
            ),
        }],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        queries = json.loads(raw)
        if isinstance(queries, list):
            return [str(q) for q in queries[:3]]
    except Exception:
        pass

    # Fallback: split visual notes into keywords
    words = visual_notes.replace(".", "").split()
    return [" ".join(words[i:i+3]) for i in range(0, min(9, len(words)), 3)][:3]
