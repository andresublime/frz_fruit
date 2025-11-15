"""
Caching layer for Peru Frozen Fruit Export MCP Server.
Provides in-memory caching for expensive queries with TTL.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
import hashlib
import json


class MCPCache:
    """
    Simple in-memory cache with TTL (Time To Live).
    Thread-safe for single-process FastMCP usage.
    """

    def __init__(self):
        """Initialize empty cache."""
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }

    def _generate_key(self, prefix: str, **kwargs) -> str:
        """
        Generate cache key from prefix and kwargs.

        Args:
            prefix: Tool name or category
            **kwargs: Parameters to hash

        Returns:
            Cache key string
        """
        # Sort kwargs for consistent hashing
        sorted_kwargs = sorted(kwargs.items())
        params_str = json.dumps(sorted_kwargs, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{prefix}:{params_hash}"

    def get(self, key: str, ttl_seconds: int = 3600) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key
            ttl_seconds: Time to live in seconds

        Returns:
            Cached value or None if expired/missing
        """
        if key not in self._cache:
            self._stats['misses'] += 1
            return None

        cached_time, cached_value = self._cache[key]

        # Check if expired
        if datetime.now() - cached_time > timedelta(seconds=ttl_seconds):
            del self._cache[key]
            self._stats['evictions'] += 1
            self._stats['misses'] += 1
            return None

        self._stats['hits'] += 1
        return cached_value

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = (datetime.now(), value)
        self._stats['sets'] += 1

    def get_or_compute(
        self,
        key: str,
        compute_fn,
        ttl_seconds: int = 3600,
        **compute_kwargs
    ) -> Any:
        """
        Get from cache or compute and cache.

        Args:
            key: Cache key
            compute_fn: Function to compute value if cache miss
            ttl_seconds: TTL in seconds
            **compute_kwargs: Arguments to pass to compute_fn

        Returns:
            Cached or computed value
        """
        cached = self.get(key, ttl_seconds)
        if cached is not None:
            return cached

        # Compute value
        value = compute_fn(**compute_kwargs)
        self.set(key, value)
        return value

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries.

        Args:
            pattern: Optional pattern to match (e.g., 'dashboard:*')
                     If None, clears entire cache

        Returns:
            Number of entries invalidated
        """
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            return count

        # Match pattern
        keys_to_delete = [
            key for key in self._cache.keys()
            if key.startswith(pattern.replace('*', ''))
        ]

        for key in keys_to_delete:
            del self._cache[key]

        return len(keys_to_delete)

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with hit rate, miss rate, and counts
        """
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'size': len(self._cache),
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'sets': self._stats['sets'],
            'evictions': self._stats['evictions'],
            'hit_rate_pct': round(hit_rate, 2),
            'total_requests': total_requests
        }

    def clear_stats(self) -> None:
        """Reset statistics counters."""
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }


# Global cache instance
_global_cache = MCPCache()


def get_cache() -> MCPCache:
    """Get global cache instance."""
    return _global_cache
