"""
OTP-related Pydantic schemas
"""
from pydantic import BaseModel, field_validator


class OTPRequest(BaseModel):
    """Schema for OTP request"""
    email: str


class OTPVerifyRequest(BaseModel):
    """Schema for OTP verification"""
    email: str
    otp_code: str


class PasswordResetWithOTP(BaseModel):
    """Schema for password reset with OTP verification"""
    email: str
    otp_code: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        """Validate new password"""
        from app.core.security import validate_password
        validate_password(v)
        return v


class OTPResponse(BaseModel):
    """Schema for OTP response"""
    message: str
    expires_in_minutes: int = 10