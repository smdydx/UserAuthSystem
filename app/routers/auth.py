"""
Authentication routes
"""
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import (
    TokenResponse, 
    RefreshTokenRequest, 
    EmailVerificationRequest,
    EmailVerificationConfirm,
    PasswordResetRequest,
    PasswordResetConfirm
)
from app.services.auth_service import AuthService
from app.utils.exceptions import CustomHTTPException

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    - **email**: Valid email address
    - **password**: Strong password meeting requirements
    - **full_name**: Optional full name
    - **role**: User role (customer, admin, vendor) - defaults to customer
    """
    auth_service = AuthService(db)
    try:
        user = auth_service.register_user(user_data, request)
        return user
    except CustomHTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token
    
    - **email**: User email address
    - **password**: User password
    
    Returns access token and refresh token
    """
    auth_service = AuthService(db)
    try:
        return auth_service.authenticate_user(login_data, request)
    except CustomHTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token
    """
    auth_service = AuthService(db)
    try:
        return auth_service.refresh_access_token(refresh_data.refresh_token, request)
    except CustomHTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Logout user by revoking refresh token
    
    - **refresh_token**: Refresh token to revoke
    """
    auth_service = AuthService(db)
    try:
        success = auth_service.logout_user(refresh_data.refresh_token)
        if success:
            return {"message": "Logged out successfully"}
        else:
            return {"message": "Token not found or already revoked"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/send-verification-email")
async def send_verification_email(
    verification_data: EmailVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Send email verification to user
    
    - **email**: Email address to verify
    """
    auth_service = AuthService(db)
    try:
        auth_service.send_email_verification(verification_data.email, request)
        return {"message": "Verification email sent successfully"}
    except CustomHTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerificationConfirm,
    db: Session = Depends(get_db)
):
    """
    Verify user email using verification token
    
    - **token**: Email verification token
    """
    auth_service = AuthService(db)
    try:
        success = auth_service.verify_email(verification_data.token)
        if success:
            return {"message": "Email verified successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email verification failed"
            )
    except CustomHTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/forgot-password")
async def forgot_password(
    reset_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Send password reset email
    
    - **email**: Email address for password reset
    """
    auth_service = AuthService(db)
    try:
        auth_service.send_password_reset(reset_data.email, request)
        return {"message": "Password reset email sent successfully"}
    except Exception as e:
        # Always return success to prevent email enumeration
        return {"message": "Password reset email sent successfully"}


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token
    
    - **token**: Password reset token
    - **new_password**: New password
    """
    auth_service = AuthService(db)
    try:
        success = auth_service.reset_password(reset_data.token, reset_data.new_password)
        if success:
            return {"message": "Password reset successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset failed"
            )
    except CustomHTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user = Depends(lambda: None)  # This will be replaced by the auth middleware
):
    """
    Get current authenticated user information
    
    Requires valid JWT token in Authorization header
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return current_user


# Health check for auth service
@router.get("/health")
async def auth_health():
    """Health check for authentication service"""
    return {"status": "healthy", "service": "authentication"}
