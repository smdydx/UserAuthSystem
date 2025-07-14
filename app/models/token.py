"""
Token models for JWT refresh tokens, email verification, and password reset
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.config import settings


class RefreshToken(Base):
    """Refresh token model"""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Token status
    is_active = Column(Boolean, default=True)
    is_revoked = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Client information
    client_ip = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (active, not revoked, not expired)"""
        return self.is_active and not self.is_revoked and not self.is_expired
    
    def revoke(self):
        """Revoke the token"""
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()


class EmailVerificationToken(Base):
    """Email verification token model"""
    __tablename__ = "email_verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Token status
    is_used = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="email_verification_tokens")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS)
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not used, not expired)"""
        return not self.is_used and not self.is_expired
    
    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.used_at = datetime.utcnow()


class PasswordResetToken(Base):
    """Password reset token model"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Token status
    is_used = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    # Client information
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_EXPIRE_HOURS)
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not used, not expired)"""
        return not self.is_used and not self.is_expired
    
    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.used_at = datetime.utcnow()
