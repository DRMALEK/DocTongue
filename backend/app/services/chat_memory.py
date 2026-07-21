from collections import defaultdict, deque
import json
import logging
from threading import Lock
from typing import Any

from app.core.config import Settings


try:
    from redis import Redis
except Exception:  # pragma: no cover - optional import guard
    Redis = None  # type: ignore[assignment]


RedisClient = Any


logger = logging.getLogger(__name__)


class ChatMemoryStore:
    """Sliding-window chat memory backed by Redis with a local fallback."""

    def __init__(self, settings: Settings) -> None:
        self._window = settings.chat_memory_window
        self._ttl_seconds = settings.chat_memory_ttl_seconds
        self._key_prefix = settings.redis_chat_key_prefix
        self._lock = Lock()
        self._local_store: dict[str, deque[dict[str, str]]] = defaultdict(
            lambda: deque(maxlen=self._window)
        )
        self._redis_client = self._connect_redis(settings.redis_url)

    def get_recent_turns(self, session_id: str, limit: int | None = None) -> list[dict[str, str]]:
        resolved_limit = min(limit or self._window, self._window)
        if self._redis_client is not None:
            key = self._session_key(session_id)
            entries = self._redis_client.lrange(key, 0, resolved_limit - 1)
            turns: list[dict[str, str]] = []
            for entry in entries:
                try:
                    parsed = json.loads(str(entry))
                except json.JSONDecodeError:
                    continue
                question = str(parsed.get("question", "")).strip()
                answer = str(parsed.get("answer", "")).strip()
                if not question:
                    continue
                turns.append({"question": question, "answer": answer})
            return turns

        with self._lock:
            entries = list(self._local_store[session_id])
        return entries[:resolved_limit]

    def get_recent_questions(self, session_id: str, limit: int | None = None) -> list[str]:
        turns = self.get_recent_turns(session_id=session_id, limit=limit)
        return [turn["question"] for turn in turns if turn.get("question")]

    def append_turn(self, session_id: str, question: str, answer: str) -> None:
        payload = json.dumps({"question": question, "answer": answer}, ensure_ascii=True)
        if self._redis_client is not None:
            key = self._session_key(session_id)
            pipe = self._redis_client.pipeline()
            pipe.lpush(key, payload)
            pipe.ltrim(key, 0, self._window - 1)
            if self._ttl_seconds > 0:
                pipe.expire(key, self._ttl_seconds)
            pipe.execute()
            return

        with self._lock:
            self._local_store[session_id].appendleft(
                {"question": question, "answer": answer}
            )

    def _connect_redis(self, redis_url: str) -> RedisClient | None:
        if Redis is None:
            logger.info("redis package not available, using in-process chat memory store")
            return None
        try:
            client = Redis.from_url(redis_url, decode_responses=True)
            client.ping()
            logger.info("Connected to Redis chat memory store at %s", redis_url)
            return client
        except Exception:
            logger.exception("Could not connect to Redis, using in-process chat memory store")
            return None

    def _session_key(self, session_id: str) -> str:
        return f"{self._key_prefix}:{session_id}"