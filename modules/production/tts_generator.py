"""
TTS Generator — converts script voiceover text to audio via ElevenLabs.
Saves audio file and updates production record.
"""

from __future__ import annotations

import hashlib
import math
import struct
import wave
from pathlib import Path

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from db.connection import execute, fetchone


class TTSGenerator:
    def __init__(self):
        self.output_dir = Path(settings.assets_dir) / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._elevenlabs_available = bool(
            settings.elevenlabs_api_key
            and settings.elevenlabs_api_key not in ("...", "")
        )

    def run(self, production_id: int) -> str | None:
        """
        Generate voiceover for the given production.
        Returns audio file path or None on failure.
        """
        production = fetchone("SELECT * FROM productions WHERE id = ?", (production_id,))
        if not production:
            logger.error(f"Production {production_id} not found.")
            return None

        script = fetchone("SELECT * FROM scripts WHERE id = ?", (production["script_id"],))
        if not script:
            logger.error(f"Script not found for production {production_id}.")
            return None

        voiceover_text = script["full_script"]
        audio_path = self._get_audio_path(production_id, voiceover_text)

        if audio_path.exists():
            logger.info(f"Audio already exists at {audio_path}, skipping TTS.")
        elif self._elevenlabs_available:
            logger.info(f"Generating TTS for production {production_id}...")
            audio_bytes = self._generate_audio(voiceover_text)
            if not audio_bytes:
                return None
            audio_path.write_bytes(audio_bytes)
            logger.info(f"Audio saved: {audio_path}")
        else:
            logger.warning("ElevenLabs not configured — generating synthetic audio placeholder.")
            audio_path = self._generate_synthetic_audio(production_id, voiceover_text)
            if not audio_path:
                return None

        execute(
            """
            UPDATE productions
            SET audio_path = ?, status = 'audio_ready', updated_at = datetime('now')
            WHERE id = ?
            """,
            (str(audio_path), production_id),
        )
        return str(audio_path)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _generate_audio(self, text: str) -> bytes | None:
        try:
            from elevenlabs import ElevenLabs
            client = ElevenLabs(api_key=settings.elevenlabs_api_key)
            audio_generator = client.text_to_speech.convert(
                voice_id=settings.elevenlabs_voice_id,
                text=text,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128",
            )
            return b"".join(audio_generator)
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            raise

    def _generate_synthetic_audio(self, production_id: int, text: str) -> Path | None:
        """
        Generate a silent WAV file sized to match the estimated script duration.
        Used as a placeholder when ElevenLabs is not configured.
        ~130 words per minute speaking rate.
        """
        words = len(text.split())
        duration = max(30, int(words / 130 * 60))  # seconds, min 30s
        sample_rate = 44100
        wav_path = self.output_dir / f"prod_{production_id}_synthetic.wav"

        try:
            with wave.open(str(wav_path), "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                n_samples = duration * sample_rate
                # Very quiet 60Hz hum so the file isn't completely silent
                frames = struct.pack(
                    f"<{n_samples}h",
                    *[int(200 * math.sin(2 * math.pi * 60 * i / sample_rate))
                      for i in range(n_samples)]
                )
                wf.writeframes(frames)
            logger.info(f"Synthetic audio ({duration}s) written to {wav_path}")
            return wav_path
        except Exception as e:
            logger.error(f"Failed to generate synthetic audio: {e}")
            return None

    def _get_audio_path(self, production_id: int, text: str) -> Path:
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        return self.output_dir / f"prod_{production_id}_{text_hash}.mp3"
