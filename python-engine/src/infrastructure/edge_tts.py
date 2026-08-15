"""Edge-TTS Async speech generation worker for SENTIENT_OS v2."""

import asyncio
import os
from pathlib import Path
from typing import Optional
import uuid
import edge_tts

from src.infrastructure.logger import get_logger

logger = get_logger("edge_tts")

VOICE_PROFILES = {
    "normal": {"rate": "+0%", "pitch": "+0Hz", "volume": "+0%"},
    "sinister": {"rate": "-15%", "pitch": "-6Hz", "volume": "+0%"},
    "whisper": {"rate": "-10%", "pitch": "-3Hz", "volume": "-25%"},
    "panicked": {"rate": "+20%", "pitch": "+4Hz", "volume": "+10%"},
    "sad": {"rate": "-10%", "pitch": "-2Hz", "volume": "-10%"},
}


class EdgeTTSWorker:
    """Generates natural neural Turkish TTS speech audio files asynchronously."""

    def __init__(
        self,
        default_voice: str = "tr-TR-AhmetNeural",
        temp_dir: str = "temp/",
    ):
        self.default_voice = default_voice
        self.temp_dir = temp_dir
        self._lock = asyncio.Lock()

        # Ensure temp directory exists
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)

    async def generate_speech(
        self,
        text: str,
        profile: str = "normal",
        voice: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate MP3 speech file from text using Edge-TTS.
        Returns relative file path to generated .mp3 file.
        """
        if not text or not text.strip():
            return None

        voice_name = voice or self.default_voice
        profile_settings = VOICE_PROFILES.get(profile, VOICE_PROFILES["normal"])

        filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
        output_path = os.path.join(self.temp_dir, filename)

        async with self._lock:
            try:
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=voice_name,
                    rate=profile_settings["rate"],
                    pitch=profile_settings["pitch"],
                    volume=profile_settings["volume"],
                )
                await communicate.save(output_path)
                logger.info(f"Generated TTS audio: '{output_path}' (profile='{profile}')")
                return output_path
            except Exception as e:
                logger.error(f"Failed to generate TTS audio with Edge-TTS: {e}")
                return None
