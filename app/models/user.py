"""
User model and related entities
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User roles enumeration"""
    CUSTOMER = "customer"
    ADMIN = "admin"
    VENDOR = "vendor"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # User status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    # Role
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Email verification
    email_verified_at = Column(DateTime, nullable=True)
    
    # Password reset
    password_reset_at = Column(DateTime, nullable=True)
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    email_verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_vendor(self) -> bool:
        """Check if user is vendor"""
        return self.role == UserRole.VENDOR
    
    @property
    def is_customer(self) -> bool:
        """Check if user is customer"""
        return self.role == UserRole.CUSTOMER
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role"""
        return self.role == role
    
    def can_access_admin(self) -> bool:
        """Check if user can access admin features"""
        return self.role in [UserRole.ADMIN]
    
    def can_access_vendor(self) -> bool:
        """Check if user can access vendor features"""
        return self.role in [UserRole.ADMIN, UserRole.VENDOR]
