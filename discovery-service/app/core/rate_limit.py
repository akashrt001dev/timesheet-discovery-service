"""
Rate Limiting for Discovery Service
Implements token bucket algorithm for request throttling
"""

from typing import Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: int, refill_interval_seconds: int = 60):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Number of tokens to add per interval
            refill_interval_seconds: Time interval for refill
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_interval_seconds = refill_interval_seconds
        self.tokens = float(capacity)
        self.last_refill = datetime.utcnow()
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds()
        refills = int(elapsed / self.refill_interval_seconds)
        
        if refills > 0:
            self.tokens = min(
                self.capacity,
                self.tokens + (refills * self.refill_rate)
            )
            self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if consumption successful, False if not enough tokens
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_remaining_tokens(self) -> float:
        """Get remaining tokens"""
        self._refill()
        return self.tokens


class RateLimiter:
    """Rate limiter using token buckets per client"""
    
    def __init__(self, default_capacity: int = 100, default_refill_rate: int = 10):
        """
        Initialize rate limiter
        
        Args:
            default_capacity: Default bucket capacity per client
            default_refill_rate: Default refill rate (tokens per minute)
        """
        self.default_capacity = default_capacity
        self.default_refill_rate = default_refill_rate
        self.buckets: Dict[str, TokenBucket] = {}
    
    def is_allowed(self, client_id: str, tokens: int = 1) -> bool:
        """
        Check if request is allowed for client
        
        Args:
            client_id: Unique client identifier (e.g., IP address)
            tokens: Number of tokens to consume
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        if client_id not in self.buckets:
            self.buckets[client_id] = TokenBucket(
                capacity=self.default_capacity,
                refill_rate=self.default_refill_rate
            )
        
        allowed = self.buckets[client_id].consume(tokens)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
        
        return allowed
    
    def get_client_status(self, client_id: str) -> Dict:
        """Get rate limit status for client"""
        if client_id not in self.buckets:
            self.buckets[client_id] = TokenBucket(
                capacity=self.default_capacity,
                refill_rate=self.default_refill_rate
            )
        
        bucket = self.buckets[client_id]
        return {
            "client_id": client_id,
            "remaining_tokens": bucket.get_remaining_tokens(),
            "capacity": bucket.capacity,
            "refill_rate": bucket.refill_rate
        }


# Rate limiters for different endpoints
registration_limiter = RateLimiter(
    default_capacity=50,      # 50 registrations per minute
    default_refill_rate=5
)

heartbeat_limiter = RateLimiter(
    default_capacity=200,     # 200 heartbeats per minute
    default_refill_rate=20
)

lookup_limiter = RateLimiter(
    default_capacity=1000,    # 1000 lookups per minute
    default_refill_rate=100
)
