"""
Rate limiting and user lockout models
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class RateLimit(Base):
    """Rate limiting model for tracking API request attempts"""
    __tablename__ = "rate_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(255), index=True, nullable=False)  # IP or email
    endpoint = Column(String(255), nullable=False)  # Which endpoint
    request_count = Column(Integer, default=1)
    
    # Time tracking
    first_request = Column(DateTime, default=datetime.utcnow)
    last_request = Column(DateTime, default=datetime.utcnow)
    reset_time = Column(DateTime, nullable=False)
    
    # Status
    is_blocked = Column(Boolean, default=False)
    blocked_until = Column(DateTime, nullable=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.reset_time:
            # Reset window is 1 hour by default
            self.reset_time = datetime.utcnow() + timedelta(hours=1)
    
    def increment_request(self):
        """Increment request count and update last request time"""
        self.request_count += 1
        self.last_request = datetime.utcnow()
    
    def is_rate_limited(self, max_requests: int = 5) -> bool:
        """Check if rate limit is exceeded"""
        if datetime.utcnow() > self.reset_time:
            # Reset the counter if time window expired
            self.request_count = 1
            self.first_request = datetime.utcnow()
            self.reset_time = datetime.utcnow() + timedelta(hours=1)
            self.is_blocked = False
            self.blocked_until = None
            return False
        
        return self.request_count > max_requests
    
    def block_requests(self, block_duration_minutes: int = 30):
        """Block requests for specified duration"""
        self.is_blocked = True
        self.blocked_until = datetime.utcnow() + timedelta(minutes=block_duration_minutes)
    
    def is_currently_blocked(self) -> bool:
        """Check if currently blocked"""
        if not self.is_blocked or not self.blocked_until:
            return False
        
        if datetime.utcnow() > self.blocked_until:
            # Unblock if block period expired
            self.is_blocked = False
            self.blocked_until = None
            return False
        
        return True


class UserLockout(Base):
    """User account lockout model for security"""
    __tablename__ = "user_lockouts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String(255), index=True, nullable=False)
    
    # Lockout details
    reason = Column(String(255), nullable=False)  # failed_login, suspicious_activity, etc.
    failed_attempts = Column(Integer, default=1)
    max_attempts = Column(Integer, default=5)
    
    # Time tracking
    first_failed_attempt = Column(DateTime, default=datetime.utcnow)
    last_failed_attempt = Column(DateTime, default=datetime.utcnow)
    locked_at = Column(DateTime, nullable=True)
    locked_until = Column(DateTime, nullable=True)
    
    # Status
    is_locked = Column(Boolean, default=False)
    is_permanent = Column(Boolean, default=False)
    
    # Security tracking
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Relations
    user = relationship("User", back_populates="lockouts")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def increment_failed_attempt(self):
        """Increment failed attempt count"""
        self.failed_attempts += 1
        self.last_failed_attempt = datetime.utcnow()
        
        # Lock account if max attempts reached
        if self.failed_attempts >= self.max_attempts:
            self.lock_account()
    
    def lock_account(self, duration_minutes: int = 30):
        """Lock user account"""
        self.is_locked = True
        self.locked_at = datetime.utcnow()
        
        if not self.is_permanent:
            self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    def unlock_account(self):
        """Unlock user account"""
        self.is_locked = False
        self.locked_until = None
        self.failed_attempts = 0
    
    def is_currently_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.is_locked:
            return False
        
        if self.is_permanent:
            return True
        
        if self.locked_until and datetime.utcnow() > self.locked_until:
            # Auto-unlock if lock period expired
            self.unlock_account()
            return False
        
        return True
    
    def time_until_unlock(self) -> timedelta:
        """Get time remaining until unlock"""
        if not self.is_currently_locked() or self.is_permanent:
            return timedelta(0)
        
        if self.locked_until:
            remaining = self.locked_until - datetime.utcnow()
            return remaining if remaining.total_seconds() > 0 else timedelta(0)
        
        return timedelta(0)