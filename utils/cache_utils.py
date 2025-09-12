import functools
import time
from typing import Any, Callable, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Cache:
    """A simple in-memory cache with time-based expiration."""
    def __init__(self, ttl: int = 300):  # Time-to-live in seconds, default 5 minutes
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """Retrieves an item from the cache if it's not expired."""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry['expiry']:
                logger.debug(f"Cache hit for key: {key}")
                return entry['value']
            else:
                logger.debug(f"Cache expired for key: {key}")
                self.delete(key)  # Remove expired item
        logger.debug(f"Cache miss for key: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Sets an item in the cache with an optional custom TTL."""
        expiry = time.time() + (ttl if ttl is not None else self.ttl)
        self.cache[key] = {'value': value, 'expiry': expiry}
        logger.debug(f"Cache set for key: {key}, expires at {expiry}")

    def delete(self, key: str):
        """Deletes an item from the cache."""
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache deleted for key: {key}")

    def clear(self):
        """Clears all items from the cache."""
        self.cache = {}
        logger.debug("Cache cleared.")

def cached(ttl: int = 300) -> Callable[..., Callable[..., Any]]:
    """Decorator to cache function results."""
    _cache = Cache(ttl)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create a cache key from function arguments
            # This simple key generation might not be suitable for all argument types (e.g., objects)
            # For more complex scenarios, consider a more robust serialization.
            key_parts = [str(arg) for arg in args]
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            cache_key = f"{func.__name__}({'_'.join(key_parts)})"

            result = _cache.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            _cache.set(cache_key, result)
            return result
        return wrapper
    return decorator

# Global cache instance for general use
# Consider creating separate cache instances for different types of data
# or more advanced caching strategies (e.g., LRU, LFU) for production systems.
global_cache = Cache()