"""
Simplified Authentication Routes - Clean E-commerce Ready APIs
"""
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import TokenResponse, RefreshTokenRequest
from app.schemas.otp import OTPRequest, OTPVerifyRequest, PasswordResetWithOTP, OTPResponse
from app.services.auth_service import AuthService
from app.services.otp_service import OTPService
from app.services.rate_limit_service import RateLimitService
from app.utils.exceptions import CustomHTTPException

router = APIRouter()


# ===== CORE AUTHENTICATION =====
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register new user - E-commerce Ready
    
    Creates user account and sends verification email
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
    User login - E-commerce Ready
    
    Returns JWT tokens for authenticated session
    """
    # Rate limiting check
    client_ip = RateLimitService.get_client_ip(request)
    is_rate_limited, _ = RateLimitService.check_login_rate_limit(
        db=db,
        identifier=client_ip,
        max_login_attempts=10,
        window_hours=1
    )
    
    if is_rate_limited:
        raise CustomHTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later.",
            error_code="RATE_LIMITED"
        )
    
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
    Refresh JWT token - E-commerce Ready
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
    User logout - E-commerce Ready
    """
    auth_service = AuthService(db)
    try:
        success = auth_service.logout_user(refresh_data.refresh_token)
        return {"message": "Logged out successfully", "success": success}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


# ===== UNIFIED PASSWORD RESET (OTP-based) =====
@router.post("/send-reset-otp", response_model=OTPResponse)
async def send_reset_otp(
    otp_data: OTPRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Send OTP for password reset - E-commerce Ready
    
    Supports both email and SMS OTP delivery
    - method: "email" or "sms"
    """
    # Rate limiting check
    is_rate_limited, _ = RateLimitService.check_otp_rate_limit(
        db=db,
        email=otp_data.email,
        max_otp_requests=3,
        window_hours=1
    )
    
    if is_rate_limited:
        raise CustomHTTPException(
            status_code=429,
            detail="Too many OTP requests. Please try again later.",
            error_code="OTP_RATE_LIMITED"
        )
    
    otp_service = OTPService(db)
    try:
        if otp_data.method == "email":
            success = otp_service.send_password_reset_otp(otp_data.email)
            message = "OTP sent to your email"
        elif otp_data.method == "sms":
            # For SMS, we need phone number from user profile
            success = otp_service.send_sms_otp_by_email(otp_data.email)
            message = "OTP sent to your phone"
        else:
            raise CustomHTTPException(
                status_code=400,
                detail="Invalid method. Use 'email' or 'sms'",
                error_code="INVALID_METHOD"
            )
        
        if success:
            return OTPResponse(
                message=message,
                expires_in_minutes=10
            )
        else:
            # Always return success to prevent email enumeration
            return OTPResponse(
                message=message,
                expires_in_minutes=10
            )
    except CustomHTTPException:
        raise
    except Exception as e:
        # Always return success to prevent information disclosure
        return OTPResponse(
            message="OTP sent successfully",
            expires_in_minutes=10
        )


@router.post("/reset-password-otp")
async def reset_password_with_otp(
    reset_data: PasswordResetWithOTP,
    db: Session = Depends(get_db)
):
    """
    Reset password using OTP - E-commerce Ready
    
    Verifies OTP and resets password in one step
    """
    otp_service = OTPService(db)
    auth_service = AuthService(db)
    
    try:
        # Verify OTP first
        if not otp_service.verify_otp(reset_data.email, reset_data.otp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Reset password
        success = auth_service.reset_password_direct(reset_data.email, reset_data.new_password)
        
        if success:
            # Mark OTP as used
            otp_service.mark_otp_as_used(reset_data.email)
            return {"message": "Password reset successfully", "success": True}
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


# ===== USER PROFILE =====
@router.get("/me", response_model=UserResponse)
async def get_current_user(
    request: Request
):
    """
    Get current user profile - E-commerce Ready
    
    Requires valid JWT token
    """
    # User is set by auth middleware
    if not hasattr(request.state, 'current_user') or not request.state.current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return request.state.current_user


# ===== HEALTH CHECK =====
@router.get("/health")
async def auth_health():
    """Health check for authentication service"""
    return {"status": "healthy", "service": "authentication"}