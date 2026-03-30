import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

CACHE_DIR = Path.home() / ".quant-agent" / "cache"


class ResponseCache:
    def __init__(self, ttl_seconds: int = 3600, enabled: bool = True):
        self.ttl = ttl_seconds
        self.enabled = enabled
        if enabled:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _key(self, query: str, model: str = "") -> str:
        raw = f"{query.strip().lower()}::{model}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _path(self, key: str) -> Path:
        return CACHE_DIR / f"{key}.json"

    def get(self, query: str, model: str = "") -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        path = self._path(self._key(query, model))
        if not path.exists():
            return None
        try:
            with open(path) as f:
                entry = json.load(f)
            if time.time() - entry.get("cached_at", 0) > self.ttl:
                path.unlink(missing_ok=True)
                return None
            logger.debug("Cache HIT for query: %s...", query[:50])
            return entry.get("data")
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def set(self, query: str, data: Dict[str, Any], model: str = "") -> None:
        if not self.enabled:
            return
        path = self._path(self._key(query, model))
        try:
            with open(path, "w") as f:
                json.dump({"cached_at": time.time(), "data": data}, f)
            logger.debug("Cache SET for query: %s...", query[:50])
        except OSError as e:
            logger.warning("Failed to write cache: %s", e)

    def clear(self) -> int:
        if not CACHE_DIR.exists():
            return 0
        count = 0
        for p in CACHE_DIR.glob("*.json"):
            p.unlink(missing_ok=True)
            count += 1
        return count
