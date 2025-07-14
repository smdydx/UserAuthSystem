"""
User-related Pydantic schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str
    role: Optional[UserRole] = UserRole.CUSTOMER
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password during creation"""
        from app.core.security import validate_password
        validate_password(v)
        return v


class UserUpdate(BaseModel):
    """Schema for user updates"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class UserProfile(BaseModel):
    """Schema for user profile"""
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class PasswordChangeRequest(BaseModel):
    """Schema for password change request"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password"""
        from app.core.security import validate_password
        validate_password(v)
        return v


class EmailChangeRequest(BaseModel):
    """Schema for email change request"""
    new_email: EmailStr
    password: str  # Require password confirmation for email changes
