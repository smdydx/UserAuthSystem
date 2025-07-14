"""
OTP model for password reset verification
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class OTPVerification(Base):
    """OTP verification model for password reset"""
    __tablename__ = "otp_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    otp_code = Column(String(6), nullable=False)  # 6 digit OTP
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Status tracking
    is_used = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    
    # Security tracking
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Relations
    user = relationship("User", back_populates="otp_verifications")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.expires_at:
            # OTP expires in 10 minutes
            self.expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    def is_expired(self) -> bool:
        """Check if OTP is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if OTP is valid (not used, not expired, attempts not exceeded)"""
        return (
            not self.is_used and 
            not self.is_expired() and 
            self.attempts < self.max_attempts
        )
    
    def increment_attempts(self):
        """Increment verification attempts"""
        self.attempts += 1
    
    def verify(self):
        """Mark OTP as verified"""
        self.is_verified = True
        self.verified_at = datetime.utcnow()
    
    def mark_as_used(self):
        """Mark OTP as used"""
        self.is_used = True