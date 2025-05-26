import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.supabase import get_supabase


class RateLimitAlgorithm(str, Enum):
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitScope(str, Enum):
    USER = "user"
    IP = "ip"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"
    GLOBAL = "global"


class RateLimitResult:
    """Result of rate limit check"""

    def __init__(
        self,
        allowed: bool,
        limit: int,
        remaining: int,
        reset_time: datetime,
        retry_after: Optional[int] = None,
    ):
        self.allowed = allowed
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time
        self.retry_after = retry_after  # seconds until next request allowed

    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers"""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_time.timestamp())),
        }

        if self.retry_after:
            headers["Retry-After"] = str(self.retry_after)

        return headers


class RateLimitConfig:
    """Rate limit configuration"""

    def __init__(
        self,
        limit: int,
        window: int,  # seconds
        algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
        scope: RateLimitScope = RateLimitScope.USER,
        burst_limit: Optional[int] = None,
        cost: int = 1,  # cost per request
    ):
        self.limit = limit
        self.window = window
        self.algorithm = algorithm
        self.scope = scope
        self.burst_limit = burst_limit or limit * 2
        self.cost = cost


class RateLimitBackend(ABC):
    """Abstract rate limit backend"""

    @abstractmethod
    async def check_limit(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check if request is within limits"""
        pass

    @abstractmethod
    async def get_usage(self, key: str) -> Dict[str, Any]:
        """Get current usage stats"""
        pass

    @abstractmethod
    async def reset_limit(self, key: str) -> bool:
        """Reset limit for key"""
        pass


class RedisRateLimitBackend(RateLimitBackend):
    """Redis-based rate limiting backend"""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_HOST
        self._redis = None

    async def get_redis(self) -> redis.Redis:
        """Get Redis connection"""
        if self._redis is None:
            self._redis = redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
        return self._redis

    async def check_limit(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check rate limit using Redis"""

        r = await self.get_redis()

        if config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return await self._sliding_window_check(r, key, config)
        elif config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return await self._token_bucket_check(r, key, config)
        elif config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return await self._fixed_window_check(r, key, config)
        else:
            raise ValueError(f"Unsupported algorithm: {config.algorithm}")

    async def _sliding_window_check(
        self, r: redis.Redis, key: str, config: RateLimitConfig
    ) -> RateLimitResult:
        """Sliding window rate limiting"""

        now = time.time()
        window_start = now - config.window

        # Use Redis pipeline for atomic operations
        pipe = r.pipeline()

        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiration
        pipe.expire(key, config.window + 1)

        results = await pipe.execute()
        current_count = results[1] + config.cost

        allowed = current_count <= config.limit
        remaining = max(0, config.limit - current_count)
        reset_time = datetime.fromtimestamp(now + config.window)

        if not allowed:
            # Remove the request we just added
            await r.zrem(key, str(now))
            retry_after = config.window
        else:
            retry_after = None

        return RateLimitResult(
            allowed=allowed,
            limit=config.limit,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
        )

    async def _token_bucket_check(
        self, r: redis.Redis, key: str, config: RateLimitConfig
    ) -> RateLimitResult:
        """Token bucket rate limiting"""

        now = time.time()
        bucket_key = f"{key}:bucket"

        # Get current bucket state
        bucket_data = await r.hgetall(bucket_key)

        if bucket_data:
            tokens = float(bucket_data.get("tokens", config.limit))
            last_refill = float(bucket_data.get("last_refill", now))
        else:
            tokens = config.limit
            last_refill = now

        # Calculate tokens to add based on time elapsed
        time_passed = now - last_refill
        tokens_to_add = (time_passed / config.window) * config.limit
        tokens = min(config.limit, tokens + tokens_to_add)

        # Check if request can be processed
        allowed = tokens >= config.cost

        if allowed:
            tokens -= config.cost

        # Update bucket state
        r.hset(bucket_key, mapping={"tokens": str(tokens), "last_refill": str(now)})
        await r.expire(bucket_key, config.window * 2)

        remaining = int(tokens)
        reset_time = datetime.fromtimestamp(now + config.window)
        retry_after = (
            None
            if allowed
            else int((config.cost - tokens) * config.window / config.limit)
        )

        return RateLimitResult(
            allowed=allowed,
            limit=config.limit,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
        )

    async def _fixed_window_check(
        self, r: redis.Redis, key: str, config: RateLimitConfig
    ) -> RateLimitResult:
        """Fixed window rate limiting"""

        now = time.time()
        window_start = int(now // config.window) * config.window
        window_key = f"{key}:{window_start}"

        # Increment counter
        current_count = await r.incr(window_key)

        # Set expiration on first increment
        if current_count == 1:
            await r.expire(window_key, config.window)

        allowed = current_count <= config.limit
        remaining = max(0, config.limit - current_count)
        reset_time = datetime.fromtimestamp(window_start + config.window)
        retry_after = None if allowed else int(reset_time.timestamp() - now)

        return RateLimitResult(
            allowed=allowed,
            limit=config.limit,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
        )

    async def get_usage(self, key: str) -> Dict[str, Any]:
        """Get usage statistics"""
        r = await self.get_redis()

        # Get all keys matching pattern
        keys = await r.keys(f"{key}*")

        usage = {}
        for k in keys:
            key_type = await r.type(k)
            if key_type == "zset":
                count = await r.zcard(k)
                usage[k] = {"type": "sliding_window", "count": count}
            elif key_type == "string":
                count = await r.get(k)
                usage[k] = {"type": "fixed_window", "count": int(count or 0)}
            elif key_type == "hash":
                data = r.hgetall(k)
                usage[k] = {"type": "token_bucket", "data": data}

        return usage

    async def reset_limit(self, key: str) -> bool:
        """Reset all limits for key"""
        r = await self.get_redis()
        keys = await r.keys(f"{key}*")
        if keys:
            await r.delete(*keys)
            return True
        return False


class InMemoryRateLimitBackend(RateLimitBackend):
    """In-memory rate limiting backend (for development/testing)"""

    def __init__(self):
        self._data = defaultdict(dict)
        self._sliding_windows = defaultdict(deque)

    async def check_limit(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check rate limit using in-memory storage"""

        if config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return await self._sliding_window_check(key, config)
        elif config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return await self._token_bucket_check(key, config)
        elif config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return await self._fixed_window_check(key, config)
        else:
            raise ValueError(f"Unsupported algorithm: {config.algorithm}")

    async def _sliding_window_check(
        self, key: str, config: RateLimitConfig
    ) -> RateLimitResult:
        """Sliding window implementation"""

        now = time.time()
        window_start = now - config.window

        # Clean old entries
        window = self._sliding_windows[key]
        while window and window[0] < window_start:
            window.popleft()

        # Check limit
        current_count = len(window) + config.cost
        allowed = current_count <= config.limit

        if allowed:
            window.append(now)

        remaining = max(0, config.limit - len(window))
        reset_time = datetime.fromtimestamp(now + config.window)
        retry_after = None if allowed else config.window

        return RateLimitResult(
            allowed=allowed,
            limit=config.limit,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
        )

    async def _token_bucket_check(
        self, key: str, config: RateLimitConfig
    ) -> RateLimitResult:
        """Token bucket implementation"""

        now = time.time()
        bucket = self._data[key]

        tokens = bucket.get("tokens", config.limit)
        last_refill = bucket.get("last_refill", now)

        # Refill tokens
        time_passed = now - last_refill
        tokens_to_add = (time_passed / config.window) * config.limit
        tokens = min(config.limit, tokens + tokens_to_add)

        # Check if request can be processed
        allowed = tokens >= config.cost

        if allowed:
            tokens -= config.cost

        # Update bucket
        bucket.update({"tokens": tokens, "last_refill": now})

        remaining = int(tokens)
        reset_time = datetime.fromtimestamp(now + config.window)
        retry_after = (
            None
            if allowed
            else int((config.cost - tokens) * config.window / config.limit)
        )

        return RateLimitResult(
            allowed=allowed,
            limit=config.limit,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
        )

    async def _fixed_window_check(
        self, key: str, config: RateLimitConfig
    ) -> RateLimitResult:
        """Fixed window implementation"""

        now = time.time()
        window_start = int(now // config.window) * config.window
        window_key = f"{window_start}"

        if window_key not in self._data[key]:
            self._data[key][window_key] = {
                "count": 0,
                "expires": window_start + config.window,
            }

        window_data = self._data[key][window_key]

        # Clean expired windows
        current_time = time.time()
        self._data[key] = {
            k: v
            for k, v in self._data[key].items()
            if v.get("expires", 0) > current_time
        }

        current_count = window_data["count"] + config.cost
        allowed = current_count <= config.limit

        if allowed:
            window_data["count"] = current_count

        remaining = max(0, config.limit - window_data["count"])
        reset_time = datetime.fromtimestamp(window_start + config.window)
        retry_after = None if allowed else int(reset_time.timestamp() - now)

        return RateLimitResult(
            allowed=allowed,
            limit=config.limit,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
        )

    async def get_usage(self, key: str) -> Dict[str, Any]:
        """Get usage statistics"""
        return dict(self._data[key])

    async def reset_limit(self, key: str) -> bool:
        """Reset limits for key"""
        if key in self._data:
            del self._data[key]
        if key in self._sliding_windows:
            del self._sliding_windows[key]
        return True


class RateLimiter:
    """Main rate limiter class"""

    def __init__(
        self,
        backend: Optional[RateLimitBackend] = None,
        default_config: Optional[RateLimitConfig] = None,
    ):
        self.backend = backend or self._get_default_backend()
        self.default_config = default_config or RateLimitConfig(
            limit=100,
            window=3600,  # 1 hour
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
        )
        self._configs = {}

    def _get_default_backend(self) -> RateLimitBackend:
        """Get default backend based on configuration"""
        if hasattr(settings, "REDIS_URL") and settings.REDIS_HOST:
            return RedisRateLimitBackend(settings.REDIS_HOST)
        else:
            return InMemoryRateLimitBackend()

    def configure(self, name: str, config: RateLimitConfig) -> None:
        """Configure a named rate limit"""
        self._configs[name] = config

    async def check_limit(
        self,
        identifier: str,
        scope: RateLimitScope = RateLimitScope.USER,
        config_name: Optional[str] = None,
        custom_config: Optional[RateLimitConfig] = None,
    ) -> RateLimitResult:
        """Check rate limit for identifier"""

        # Get configuration
        if custom_config:
            config = custom_config
        elif config_name and config_name in self._configs:
            config = self._configs[config_name]
        else:
            config = self.default_config

        # Create rate limit key
        key = f"rate_limit:{scope.value}:{identifier}"

        # Check limit
        result = await self.backend.check_limit(key, config)

        # Log rate limit check
        await self._log_rate_limit_check(identifier, scope, result)

        return result

    async def get_usage(
        self, identifier: str, scope: RateLimitScope = RateLimitScope.USER
    ) -> Dict[str, Any]:
        """Get usage statistics"""
        key = f"rate_limit:{scope.value}:{identifier}"
        return await self.backend.get_usage(key)

    async def reset_limit(
        self, identifier: str, scope: RateLimitScope = RateLimitScope.USER
    ) -> bool:
        """Reset rate limit for identifier"""
        key = f"rate_limit:{scope.value}:{identifier}"
        success = await self.backend.reset_limit(key)

        if success:
            await self._log_rate_limit_reset(identifier, scope)

        return success

    async def _log_rate_limit_check(
        self, identifier: str, scope: RateLimitScope, result: RateLimitResult
    ) -> None:
        """Log rate limit check for monitoring"""
        try:
            supabase = await get_supabase()

            log_data = {
                "identifier": identifier,
                "scope": scope.value,
                "allowed": result.allowed,
                "limit_value": result.limit,
                "remaining": result.remaining,
                "timestamp": datetime.now().isoformat(),
            }

            await supabase.table("rate_limiter_logs").insert(log_data).execute()

        except Exception as e:
            # Don't let logging failures affect rate limiting
            print(f"Failed to log rate limit check: {e}")

    async def _log_rate_limit_reset(
        self, identifier: str, scope: RateLimitScope
    ) -> None:
        """Log rate limit reset"""
        try:
            supabase = await get_supabase()

            log_data = {
                "identifier": identifier,
                "scope": scope.value,
                "action": "reset",
                "timestamp": datetime.now().isoformat(),
            }

            await supabase.table("rate_limit_logs").insert(log_data).execute()

        except Exception:
            pass


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()

        # Configure default rate limits
        _rate_limiter.configure(
            "api_standard",
            RateLimitConfig(
                limit=1000, window=3600, algorithm=RateLimitAlgorithm.SLIDING_WINDOW
            ),
        )

        _rate_limiter.configure(
            "api_premium",
            RateLimitConfig(
                limit=5000, window=3600, algorithm=RateLimitAlgorithm.TOKEN_BUCKET
            ),
        )

        _rate_limiter.configure(
            "api_burst",
            RateLimitConfig(
                limit=100, window=60, algorithm=RateLimitAlgorithm.SLIDING_WINDOW
            ),
        )

        _rate_limiter.configure(
            "search_heavy",
            RateLimitConfig(
                limit=50,
                window=300,  # 5 minutes
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                cost=2,  # Each search request costs 2 tokens
            ),
        )

    return _rate_limiter


# Convenience functions
async def check_rate_limit(
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    api_key_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    limit: Optional[int] = None,
    window: Optional[int] = None,
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
) -> bool:
    """Simplified rate limit check function"""

    limiter = get_rate_limiter()

    # Determine identifier and scope
    if user_id:
        identifier = user_id
        scope = RateLimitScope.USER
    elif api_key_id:
        identifier = api_key_id
        scope = RateLimitScope.API_KEY
    elif ip_address:
        identifier = ip_address
        scope = RateLimitScope.IP
    elif endpoint:
        identifier = endpoint
        scope = RateLimitScope.ENDPOINT
    else:
        identifier = "global"
        scope = RateLimitScope.GLOBAL

    # Use custom config if provided
    custom_config = None
    if limit and window:
        custom_config = RateLimitConfig(limit=limit, window=window, algorithm=algorithm)

    result = await limiter.check_limit(
        identifier=identifier, scope=scope, custom_config=custom_config
    )

    return result.allowed


async def get_rate_limit_info(
    user_id: Optional[str] = None, ip_address: Optional[str] = None, api_key_id: Optional[str] = None
) -> RateLimitResult:
    """Get rate limit information without consuming quota"""

    limiter = get_rate_limiter()

    # Determine identifier and scope
    if user_id:
        identifier = user_id
        scope = RateLimitScope.USER
    elif api_key_id:
        identifier = api_key_id
        scope = RateLimitScope.API_KEY
    elif ip_address:
        identifier = ip_address
        scope = RateLimitScope.IP
    else:
        identifier = "global"
        scope = RateLimitScope.GLOBAL

    # Check with cost = 0 to get info without consuming quota
    config = RateLimitConfig(limit=1000, window=3600, cost=0)  # Don't consume quota

    return await limiter.check_limit(
        identifier=identifier, scope=scope, custom_config=config
    )
