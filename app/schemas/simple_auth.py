"""
Simple authentication schemas for e-commerce
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class SimpleLogin(BaseModel):
    """Simple login request"""
    email: EmailStr
    password: str


class SimpleRegister(BaseModel):
    """Simple registration request"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None


class SimpleOTPRequest(BaseModel):
    """Simple OTP request for password reset"""
    email: EmailStr
    method: str = "email"  # "email" or "sms"


class SimplePasswordReset(BaseModel):
    """Simple password reset with OTP"""
    email: EmailStr
    otp_code: str
    new_password: str


class SimpleResponse(BaseModel):
    """Simple response format"""
    message: str
    success: bool = True
    data: Optional[dict] = None