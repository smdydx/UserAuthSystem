"""
Token-related Pydantic schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Base token schema"""
    access_token: str
    token_type: str = "bearer"


class TokenResponse(Token):
    """Extended token response with refresh token"""
    refresh_token: str
    expires_in: int  # Access token expiration in seconds
    user: dict


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str


class EmailVerificationRequest(BaseModel):
    """Schema for email verification request"""
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    """Schema for email verification confirmation"""
    token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password"""
        from app.core.security import validate_password
        validate_password(v)
        return v


class TokenInfo(BaseModel):
    """Schema for token information"""
    token: str
    token_type: str
    created_at: datetime
    expires_at: datetime
    is_active: bool
    is_revoked: Optional[bool] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        orm_mode = True
