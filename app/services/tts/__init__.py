import asyncio
import logging
import threading
from collections.abc import AsyncIterator

from app.core.config import get_settings
from app.services.tts.engine import TTSEngine

logger = logging.getLogger(__name__)

_SENTINEL = object()


class TTSService:
    def __init__(self) -> None:
        self._engine = TTSEngine()

    def load(self) -> None:
        settings = get_settings()
        if not settings.TTS_ENABLED:
            logger.info("TTS disabled via TTS_ENABLED=false")
            return
        self._engine.load()

    def is_ready(self) -> bool:
        settings = get_settings()
        if not settings.TTS_ENABLED:
            return False
        return self._engine.is_ready

    async def stream_speech(self, text: str, return_visemes: bool) -> AsyncIterator[bytes]:
        if not self.is_ready():
            raise RuntimeError("TTS is not available")

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[object] = asyncio.Queue()

        def _produce() -> None:
            try:
                for line in self._engine.stream_chunks(text, return_visemes):
                    loop.call_soon_threadsafe(queue.put_nowait, line)
            except Exception as exc:
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, _SENTINEL)

        thread = threading.Thread(target=_produce, daemon=True)
        thread.start()

        while True:
            item = await queue.get()
            if item is _SENTINEL:
                break
            if isinstance(item, Exception):
                raise item
            yield item.encode("utf-8")


_tts_service: TTSService | None = None


def get_tts_service() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
