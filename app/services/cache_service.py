
"""
Advanced Caching Service for FastAPI
"""
import json
import time
from typing import Any, Optional, Dict
from functools import wraps
import hashlib

class AdvancedCache:
    """In-memory cache with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache: Dict[str, Dict] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments"""
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_expired(self, item: dict) -> bool:
        """Check if cache item is expired"""
        return time.time() > item['expires_at']
    
    def _evict_expired(self):
        """Remove expired items"""
        current_time = time.time()
        expired_keys = [k for k, v in self.cache.items() if current_time > v['expires_at']]
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_lru(self):
        """Remove least recently used items if cache is full"""
        if len(self.cache) >= self.max_size:
            # Sort by last_accessed and remove oldest
            lru_key = min(self.cache.keys(), key=lambda k: self.cache[k]['last_accessed'])
            del self.cache[lru_key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            if self._is_expired(self.cache[key]):
                del self.cache[key]
                return None
            
            # Update last accessed
            self.cache[key]['last_accessed'] = time.time()
            return self.cache[key]['data']
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache"""
        self._evict_expired()
        self._evict_lru()
        
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'data': value,
            'expires_at': time.time() + ttl,
            'last_accessed': time.time()
        }
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()

# Global cache instance
cache = AdvancedCache()

def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Usage:
    @cached(ttl=600, key_prefix="products")
    async def get_products():
        return await fetch_products()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            func_name = f"{key_prefix}:{func.__name__}" if key_prefix else func.__name__
            cache_key = cache._generate_key(func_name, args, kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

def cache_key_builder(prefix: str, **params) -> str:
    """Build cache key from parameters"""
    key_parts = [prefix]
    for k, v in sorted(params.items()):
        key_parts.append(f"{k}:{v}")
    return ":".join(key_parts)
