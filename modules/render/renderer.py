"""
Renderer — assembles final Short video from audio + subtitles + background.

Pipeline:
  1. Load background clip (stock footage or gradient fallback)
  2. Generate subtitle clips from script on-screen segments
  3. Mix voiceover audio + background music
  4. Composite everything → 1080x1920 MP4
  5. Save to output/ and update production record

Requires: FFmpeg installed on system PATH.
Uses MoviePy 2.x API.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from loguru import logger
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
    vfx,
)
from moviepy.audio.AudioClip import CompositeAudioClip

from config.settings import settings
from db.connection import execute, fetchone


W, H = 1080, 1920
FPS = 30

# Font to use for text overlays
import os as _os
DEFAULT_FONT = (
    "C:/Windows/Fonts/arialbd.ttf"
    if _os.path.exists("C:/Windows/Fonts/arialbd.ttf")
    else "Arial-Bold"
)


class Renderer:
    def __init__(self):
        self.output_dir = Path(settings.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir = Path(settings.assets_dir)

    def run(self, production_id: int) -> str | None:
        """
        Render the video for production_id.
        Returns output video path or None on failure.
        """
        production = fetchone("SELECT * FROM productions WHERE id = ?", (production_id,))
        if not production:
            logger.error(f"Production {production_id} not found.")
            return None

        production = dict(production)
        script = fetchone("SELECT * FROM scripts WHERE id = ?", (production["script_id"],))
        if not script:
            return None
        script = dict(script)

        audio_path = production.get("audio_path")
        if not audio_path or not Path(audio_path).exists():
            logger.error(f"Audio not found for production {production_id}.")
            return None

        logger.info(f"Rendering production {production_id}...")
        execute(
            "UPDATE productions SET status = 'rendering', updated_at = datetime('now') WHERE id = ?",
            (production_id,),
        )

        try:
            output_path = self._render(production, script, audio_path)
        except Exception as e:
            logger.error(f"Render failed for production {production_id}: {e}")
            execute(
                "UPDATE productions SET status = 'failed', error_message = ?, updated_at = datetime('now') WHERE id = ?",
                (str(e), production_id),
            )
            return None

        duration = self._get_duration(output_path)
        execute(
            """
            UPDATE productions
            SET video_path = ?, duration_actual = ?, status = 'rendered',
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (str(output_path), duration, production_id),
        )
        logger.info(f"Rendered: {output_path} ({duration:.1f}s)")
        return str(output_path)

    def _render(self, production: dict, script: dict, audio_path: str) -> Path:
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        # Background
        bg = self._get_background(production, duration)

        # Subtitle text clips
        onscreen = json.loads(script.get("onscreen_segments", "[]"))
        text_clips = self._build_text_clips(onscreen, duration)

        # Background music
        bg_music_path = self._find_music(script.get("music_mood", ""))
        if bg_music_path:
            try:
                bg_music = AudioFileClip(str(bg_music_path))
                bg_music = bg_music.subclipped(0, min(duration, bg_music.duration))
                bg_music = bg_music.with_volume_scaled(0.08)
                final_audio = CompositeAudioClip([audio_clip, bg_music])
            except Exception as e:
                logger.warning(f"Failed to load background music: {e}")
                final_audio = audio_clip
        else:
            final_audio = audio_clip

        # Composite
        cta_clip = self._build_cta_clip(duration)
        layers = [bg] + text_clips + ([cta_clip] if cta_clip else [])
        video = CompositeVideoClip(layers, size=(W, H))
        video = video.with_audio(final_audio)
        video = video.with_duration(duration)

        output_path = self.output_dir / f"prod_{production['id']}.mp4"
        video.write_videofile(
            str(output_path),
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            bitrate="4000k",
            audio_bitrate="192k",
            threads=4,
            preset="fast",
            logger=None,
        )
        return output_path

    def _get_background(self, production: dict, duration: float):
        broll_paths = json.loads(production.get("broll_paths", "[]"))

        if broll_paths:
            clips = []
            for p in broll_paths:
                if Path(p).exists():
                    try:
                        c = VideoFileClip(p).resized((W, H))
                        clips.append(c)
                    except Exception:
                        pass
            if clips:
                bg = concatenate_videoclips(clips)
                if bg.duration < duration:
                    bg = bg.with_effects([vfx.Loop(duration=duration)])
                bg = bg.with_duration(duration)
                return bg

        # Fallback: dark gradient background
        return ColorClip(size=(W, H), color=(15, 15, 20)).with_duration(duration)

    def _build_text_clips(self, onscreen: list, total_duration: float) -> list:
        clips = []
        if not onscreen:
            return clips

        segment_duration = total_duration / max(len(onscreen), 1)

        for i, seg in enumerate(onscreen):
            start = i * segment_duration
            end = min(start + segment_duration, total_duration)

            try:
                txt = TextClip(
                    font=DEFAULT_FONT,
                    text=seg["text"] + "\n",
                    font_size=68,
                    color="white",
                    stroke_color="black",
                    stroke_width=3,
                    size=(W - 120, None),
                    method="caption",
                    text_align="center",
                    duration=(end - start),
                )
                # Center horizontally; anchor vertically so text is centered around H*0.45
                txt = txt.with_position(lambda t: ("center", max(60, H // 2 - txt.h // 2)))
                txt = txt.with_start(start)
                clips.append(txt)
            except Exception as e:
                logger.warning(f"Failed to create text clip for segment {i}: {e}")

        return clips

    def _build_cta_clip(self, duration: float):
        """Build a subscribe CTA overlay for the final 4 seconds."""
        cta_start = max(0, duration - 4.0)
        cta_duration = duration - cta_start
        try:
            cta = TextClip(
                font=DEFAULT_FONT,
                text="New psychology daily  •  subscribe WiredWrong\n",
                font_size=40,
                color="white",
                stroke_color="black",
                stroke_width=2,
                method="label",
                text_align="left",
            )
            cta = cta.with_duration(cta_duration)
            cta = cta.with_effects([vfx.CrossFadeIn(0.4)])
            cta = cta.with_start(cta_start)
            cta = cta.with_position((60, 1640))
            return cta
        except Exception as e:
            from loguru import logger
            logger.warning(f"Failed to build CTA clip: {e}")
            return None

    def _find_music(self, mood: str) -> Path | None:
        music_dir = self.assets_dir / "music"
        if not music_dir.exists():
            return None
        mood_map = {
            "dark ambient": "dark_ambient",
            "tense": "tense",
            "calm curious": "calm",
        }
        folder_name = mood_map.get(mood, "dark_ambient")
        folder = music_dir / folder_name
        if folder.exists():
            tracks = list(folder.glob("*.mp3"))
            if tracks:
                import random
                return random.choice(tracks)
        all_tracks = list(music_dir.rglob("*.mp3"))
        return all_tracks[0] if all_tracks else None

    def _get_duration(self, path: Path) -> float:
        try:
            import imageio_ffmpeg
            import json as _json
            # Use bundled ffmpeg; derive ffprobe path from ffmpeg path
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            ffprobe_exe = ffmpeg_exe.replace("ffmpeg", "ffprobe")
            import os
            if not os.path.exists(ffprobe_exe):
                # Fallback: ask ffmpeg itself for duration via stderr
                result = subprocess.run(
                    [ffmpeg_exe, "-i", str(path)],
                    capture_output=True, text=True,
                )
                import re
                match = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", result.stderr)
                if match:
                    h, m, s = match.groups()
                    return int(h) * 3600 + int(m) * 60 + float(s)
            else:
                result = subprocess.run(
                    [ffprobe_exe, "-v", "quiet", "-print_format", "json",
                     "-show_streams", str(path)],
                    capture_output=True, text=True,
                )
                data = _json.loads(result.stdout)
                for stream in data.get("streams", []):
                    if stream.get("duration"):
                        return float(stream["duration"])
        except Exception:
            pass
        return 0.0
