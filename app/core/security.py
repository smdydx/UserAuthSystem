"""
Security utilities for password hashing and JWT token management
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets

from app.core.config import settings
from app.utils.exceptions import CustomHTTPException


# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def validate_password(password: str) -> bool:
    """
    Validate password strength based on configured requirements
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise CustomHTTPException(
            status_code=400,
            detail=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long",
            error_code="PASSWORD_TOO_SHORT"
        )
    
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        raise CustomHTTPException(
            status_code=400,
            detail="Password must contain at least one uppercase letter",
            error_code="PASSWORD_NO_UPPERCASE"
        )
    
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        raise CustomHTTPException(
            status_code=400,
            detail="Password must contain at least one lowercase letter",
            error_code="PASSWORD_NO_LOWERCASE"
        )
    
    if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', password):
        raise CustomHTTPException(
            status_code=400,
            detail="Password must contain at least one number",
            error_code="PASSWORD_NO_NUMBERS"
        )
    
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        raise CustomHTTPException(
            status_code=400,
            detail="Password must contain at least one special character",
            error_code="PASSWORD_NO_SPECIAL"
        )
    
    return True


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verify and decode JWT token
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            raise CustomHTTPException(
                status_code=401,
                detail="Invalid token type",
                error_code="INVALID_TOKEN_TYPE"
            )
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise CustomHTTPException(
                status_code=401,
                detail="Token has expired",
                error_code="TOKEN_EXPIRED"
            )
        
        return payload
        
    except JWTError as e:
        raise CustomHTTPException(
            status_code=401,
            detail="Could not validate credentials",
            error_code="INVALID_TOKEN"
        )


def generate_email_verification_token() -> str:
    """Generate a secure token for email verification"""
    return secrets.token_urlsafe(32)


def generate_password_reset_token() -> str:
    """Generate a secure token for password reset"""
    return secrets.token_urlsafe(32)


def create_email_verification_token(email: str) -> str:
    """Create JWT token for email verification"""
    expire = datetime.utcnow() + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS)
    to_encode = {
        "email": email,
        "exp": expire,
        "type": "email_verification"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_password_reset_token(email: str) -> str:
    """Create JWT token for password reset"""
    expire = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_EXPIRE_HOURS)
    to_encode = {
        "email": email,
        "exp": expire,
        "type": "password_reset"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
