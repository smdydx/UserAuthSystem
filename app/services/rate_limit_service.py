"""
Advanced Rate limiting service for API endpoints
"""
import time
from typing import Dict, Tuple, Optional
import logging
import hashlib
from enum import Enum
from dataclasses import dataclass, field

from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitType(str, Enum):
    PER_SECOND = "per_second"
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"

@dataclass
class RateLimitRule:
    limit: int
    window: int  # seconds
    rule_type: RateLimitType
    burst_limit: Optional[int] = None  # Allow burst requests

@dataclass
class UserRateLimitTracker:
    requests: list = field(default_factory=list)
    burst_tokens: int = 0
    last_refill: float = field(default_factory=time.time)

class AdvancedRateLimitService:
    """Service for managing rate limits and user lockouts"""

    @staticmethod
    def check_rate_limit(
        db: Session,
        identifier: str,
        endpoint: str,
        max_requests: int = 5,
        window_hours: int = 1
    ) -> Tuple[bool, Optional[RateLimit]]:
        """
        Check if request is rate limited

        Args:
            db: Database session
            identifier: IP address or email
            endpoint: API endpoint being accessed
            max_requests: Maximum requests allowed in window
            window_hours: Time window in hours

        Returns:
            Tuple of (is_rate_limited, rate_limit_record)
        """
        # Get existing rate limit record
        rate_limit = db.query(RateLimit).filter(
            RateLimit.identifier == identifier,
            RateLimit.endpoint == endpoint
        ).first()

        if not rate_limit:
            # Create new rate limit record
            rate_limit = RateLimit(
                identifier=identifier,
                endpoint=endpoint,
                request_count=1,
                reset_time=datetime.utcnow() + timedelta(hours=window_hours)
            )
            db.add(rate_limit)
            db.commit()
            db.refresh(rate_limit)
            return False, rate_limit

        # Check if currently blocked
        if rate_limit.is_currently_blocked():
            logger.warning(f"Request blocked for {identifier} on {endpoint} - currently in block period")
            return True, rate_limit

        # Check rate limit
        if rate_limit.is_rate_limited(max_requests):
            # Block the identifier
            rate_limit.block_requests(block_duration_minutes=30)
            db.commit()
            logger.warning(f"Rate limit exceeded for {identifier} on {endpoint} - blocking for 30 minutes")
            return True, rate_limit

        # Increment request count
        rate_limit.increment_request()
        db.commit()

        return False, rate_limit

    @staticmethod
    def check_otp_rate_limit(
        db: Session,
        email: str,
        max_otp_requests: int = 3,
        window_hours: int = 1
    ) -> Tuple[bool, Optional[RateLimit]]:
        """
        Check OTP-specific rate limit
        """
        return RateLimitService.check_rate_limit(
            db=db,
            identifier=email,
            endpoint="/otp-request",
            max_requests=max_otp_requests,
            window_hours=window_hours
        )

    @staticmethod
    def check_login_rate_limit(
        db: Session,
        identifier: str,  # IP or email
        max_login_attempts: int = 10,
        window_hours: int = 1
    ) -> Tuple[bool, Optional[RateLimit]]:
        """
        Check login-specific rate limit
        """
        return RateLimitService.check_rate_limit(
            db=db,
            identifier=identifier,
            endpoint="/login",
            max_requests=max_login_attempts,
            window_hours=window_hours
        )

    @staticmethod
    def track_failed_login(
        db: Session,
        user_id: int,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        max_attempts: int = 5,
        lockout_duration_minutes: int = 30
    ) -> UserLockout:
        """
        Track failed login attempt and potentially lock account
        """
        # Get existing lockout record
        lockout = db.query(UserLockout).filter(
            UserLockout.user_id == user_id,
            UserLockout.reason == "failed_login"
        ).first()

        if not lockout:
            # Create new lockout record
            lockout = UserLockout(
                user_id=user_id,
                email=email,
                reason="failed_login",
                failed_attempts=1,
                max_attempts=max_attempts,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(lockout)
        else:
            # Increment existing lockout
            lockout.increment_failed_attempt()
            if ip_address:
                lockout.ip_address = ip_address
            if user_agent:
                lockout.user_agent = user_agent

        db.commit()
        db.refresh(lockout)

        if lockout.is_currently_locked():
            logger.warning(f"User {email} locked due to failed login attempts")

        return lockout

    @staticmethod
    def check_user_lockout(db: Session, user_id: int, email: str) -> Optional[UserLockout]:
        """
        Check if user account is currently locked
        """
        lockout = db.query(UserLockout).filter(
            UserLockout.user_id == user_id,
            UserLockout.is_locked == True
        ).first()

        if lockout and lockout.is_currently_locked():
            return lockout

        return None

    @staticmethod
    def unlock_user_account(db: Session, user_id: int, reason: str = "manual_unlock"):
        """
        Manually unlock user account
        """
        lockouts = db.query(UserLockout).filter(
            UserLockout.user_id == user_id,
            UserLockout.is_locked == True
        ).all()

        for lockout in lockouts:
            lockout.unlock_account()

        db.commit()
        logger.info(f"User account {user_id} unlocked manually - reason: {reason}")

    @staticmethod
    def clear_successful_login(db: Session, user_id: int):
        """
        Clear failed login attempts after successful login
        """
        lockouts = db.query(UserLockout).filter(
            UserLockout.user_id == user_id,
            UserLockout.reason == "failed_login",
            UserLockout.is_locked == False
        ).all()

        for lockout in lockouts:
            lockout.failed_attempts = 0
            lockout.first_failed_attempt = datetime.utcnow()
            lockout.last_failed_attempt = datetime.utcnow()

        db.commit()

    @staticmethod
    def get_client_ip(request: Request) -> str:
        """
        Get client IP address from request
        """
        # Check for forwarded IP (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP if multiple are present
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        if hasattr(request.client, 'host'):
            return request.client.host

        return "unknown"

    @staticmethod
    def get_user_agent(request: Request) -> str:
        """
        Get user agent from request
        """
        return request.headers.get("User-Agent", "unknown")[:500]  # Limit length