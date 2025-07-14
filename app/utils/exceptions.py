"""
Custom exception classes for better error handling
"""
from datetime import datetime
from typing import Optional, Any, Dict
from fastapi import HTTPException


class CustomHTTPException(HTTPException):
    """
    Custom HTTP exception with additional error information
    """
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        timestamp: Optional[datetime] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.timestamp = timestamp or datetime.utcnow()
        self.extra_data = extra_data or {}


class AuthenticationError(CustomHTTPException):
    """Authentication related errors"""
    
    def __init__(self, detail: str = "Authentication failed", error_code: str = "AUTHENTICATION_FAILED"):
        super().__init__(status_code=401, detail=detail, error_code=error_code)


class AuthorizationError(CustomHTTPException):
    """Authorization related errors"""
    
    def __init__(self, detail: str = "Insufficient permissions", error_code: str = "INSUFFICIENT_PERMISSIONS"):
        super().__init__(status_code=403, detail=detail, error_code=error_code)


class ValidationError(CustomHTTPException):
    """Validation related errors"""
    
    def __init__(self, detail: str = "Validation failed", error_code: str = "VALIDATION_ERROR"):
        super().__init__(status_code=400, detail=detail, error_code=error_code)


class NotFoundError(CustomHTTPException):
    """Resource not found errors"""
    
    def __init__(self, detail: str = "Resource not found", error_code: str = "RESOURCE_NOT_FOUND"):
        super().__init__(status_code=404, detail=detail, error_code=error_code)


class ConflictError(CustomHTTPException):
    """Resource conflict errors"""
    
    def __init__(self, detail: str = "Resource conflict", error_code: str = "RESOURCE_CONFLICT"):
        super().__init__(status_code=409, detail=detail, error_code=error_code)


class InternalServerError(CustomHTTPException):
    """Internal server errors"""
    
    def __init__(self, detail: str = "Internal server error", error_code: str = "INTERNAL_SERVER_ERROR"):
        super().__init__(status_code=500, detail=detail, error_code=error_code)


# Error code constants
class ErrorCodes:
    """Centralized error codes"""
    
    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN_TYPE = "INVALID_TOKEN_TYPE"
    INVALID_REFRESH_TOKEN = "INVALID_REFRESH_TOKEN"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    
    # Authorization errors
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ACCESS_DENIED = "ACCESS_DENIED"
    ROLE_REQUIRED = "ROLE_REQUIRED"
    
    # User errors
    USER_NOT_FOUND = "USER_NOT_FOUND"
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    EMAIL_NOT_VERIFIED = "EMAIL_NOT_VERIFIED"
    EMAIL_ALREADY_VERIFIED = "EMAIL_ALREADY_VERIFIED"
    
    # Password errors
    PASSWORD_TOO_SHORT = "PASSWORD_TOO_SHORT"
    PASSWORD_NO_UPPERCASE = "PASSWORD_NO_UPPERCASE"
    PASSWORD_NO_LOWERCASE = "PASSWORD_NO_LOWERCASE"
    PASSWORD_NO_NUMBERS = "PASSWORD_NO_NUMBERS"
    PASSWORD_NO_SPECIAL = "PASSWORD_NO_SPECIAL"
    INVALID_CURRENT_PASSWORD = "INVALID_CURRENT_PASSWORD"
    
    # Token errors
    INVALID_VERIFICATION_TOKEN = "INVALID_VERIFICATION_TOKEN"
    INVALID_RESET_TOKEN = "INVALID_RESET_TOKEN"
    
    # System errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EMAIL_SEND_FAILED = "EMAIL_SEND_FAILED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    CANNOT_DELETE_LAST_ADMIN = "CANNOT_DELETE_LAST_ADMIN"
    CANNOT_DEACTIVATE_LAST_ADMIN = "CANNOT_DEACTIVATE_LAST_ADMIN"
