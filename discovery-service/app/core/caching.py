"""
Caching layer for Discovery Service
Implements TTL-based caching for frequently accessed data
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a cached entry with TTL"""
    
    def __init__(self, value: Any, ttl_seconds: int = 30):
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry_time


class DiscoveryCache:
    """Simple in-memory cache for discovery data"""
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    return entry.value
                else:
                    # Remove expired entry
                    del self._cache[key]
                    return None
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 30):
        """Set value in cache with TTL"""
        async with self._lock:
            self._cache[key] = CacheEntry(value, ttl_seconds)
            logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
    
    async def invalidate(self, key: str):
        """Invalidate a cache entry"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache invalidated: {key}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all cache entries matching a pattern"""
        async with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
                logger.debug(f"Cache invalidated: {key}")
    
    async def clear(self):
        """Clear all cache"""
        async with self._lock:
            self._cache.clear()
            logger.debug("Cache cleared")
    
    async def get_size(self) -> int:
        """Get current cache size"""
        return len(self._cache)


# Global cache instance
_cache_instance: Optional[DiscoveryCache] = None


def get_cache() -> DiscoveryCache:
    """Get or create global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DiscoveryCache()
    return _cache_instance


def cached(key_prefix: str, ttl: int = 30):
    """Decorator for caching async function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Build cache key
            cache_key = f"{key_prefix}:{':'.join(str(arg) for arg in args)}"
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                from app.core.metrics import cache_hits_total
                cache_hits_total.labels(cache_type=key_prefix).inc()
                return cached_value
            
            # Cache miss - execute function
            logger.debug(f"Cache miss: {cache_key}")
            from app.core.metrics import cache_misses_total
            cache_misses_total.labels(cache_type=key_prefix).inc()
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator
