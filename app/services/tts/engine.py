import base64
import io
import json
import logging
from collections.abc import Iterator

import soundfile as sf
from kokoro import KPipeline

from app.core.config import get_settings
from app.services.tts.visemes import generate_viseme_chunk

logger = logging.getLogger(__name__)

SAMPLE_RATE = 24000


class TTSEngine:
    def __init__(self) -> None:
        self._pipeline: KPipeline | None = None
        self._voice = None
        self._ready = False

    @property
    def is_ready(self) -> bool:
        return self._ready

    def load(self) -> None:
        settings = get_settings()
        logger.info("Loading Kokoro TTS pipeline (lang=%s)...", settings.TTS_LANG_CODE)
        pipeline = KPipeline(lang_code=settings.TTS_LANG_CODE)
        voice_male = pipeline.load_voice("am_puck")
        voice_female = pipeline.load_voice("af_bella")
        young_boy_voice = (voice_male * 0.6) + (voice_female * 0.4)

        self._pipeline = pipeline
        self._voice = young_boy_voice
        self._ready = True
        logger.info("Kokoro TTS pipeline ready")

    def stream_chunks(self, text: str, return_visemes: bool) -> Iterator[str]:
        if not self._ready or self._pipeline is None or self._voice is None:
            raise RuntimeError("TTS engine is not loaded")

        settings = get_settings()
        generator = self._pipeline(text, voice=self._voice, speed=settings.TTS_SPEED)
        current_global_time = 0.0

        for _graphemes, phonemes, audio in generator:
            buffer = io.BytesIO()
            sf.write(buffer, audio, SAMPLE_RATE, format="WAV")
            audio_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            chunk_data: dict = {"audio": audio_b64}

            if return_visemes:
                viseme_chunk, current_global_time = generate_viseme_chunk(
                    phonemes=phonemes,
                    audio_length=len(audio),
                    sample_rate=SAMPLE_RATE,
                    start_time=current_global_time,
                )
                chunk_data["visemes"] = viseme_chunk

            yield json.dumps(chunk_data) + "\n"
