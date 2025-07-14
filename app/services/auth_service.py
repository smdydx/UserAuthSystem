"""
Authentication service for handling user authentication logic
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request

from app.models.user import User, UserRole
from app.models.token import RefreshToken, EmailVerificationToken, PasswordResetToken
from app.schemas.user import UserCreate, UserLogin
from app.schemas.token import TokenResponse
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    verify_token,
    create_email_verification_token,
    create_password_reset_token
)
from app.core.config import settings
from app.utils.exceptions import CustomHTTPException
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service class"""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
    
    def register_user(self, user_data: UserCreate, request: Request) -> User:
        """
        Register a new user
        """
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise CustomHTTPException(
                status_code=400,
                detail="Email already registered",
                error_code="EMAIL_ALREADY_EXISTS"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role or UserRole.CUSTOMER,
            is_active=True,
            is_verified=False
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Send email verification
        try:
            self._send_email_verification(user, request)
        except Exception as e:
            logger.warning(f"Failed to send email verification: {str(e)}")
        
        logger.info(f"User registered successfully: {user.email}")
        return user
    
    def authenticate_user(self, login_data: UserLogin, request: Request) -> TokenResponse:
        """
        Authenticate user and return tokens
        """
        # Find user by email
        user = self.db.query(User).filter(User.email == login_data.email).first()
        if not user:
            raise CustomHTTPException(
                status_code=401,
                detail="Invalid email or password",
                error_code="INVALID_CREDENTIALS"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise CustomHTTPException(
                status_code=401,
                detail="Invalid email or password",
                error_code="INVALID_CREDENTIALS"
            )
        
        # Check if user is active
        if not user.is_active:
            raise CustomHTTPException(
                status_code=401,
                detail="Account is disabled",
                error_code="ACCOUNT_DISABLED"
            )
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        refresh_token_str = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Store refresh token in database
        refresh_token = RefreshToken(
            token=refresh_token_str,
            user_id=user.id,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent")
        )
        self.db.add(refresh_token)
        
        # Update last login
        user.last_login = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"User authenticated successfully: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_verified": user.is_verified
            }
        )
    
    def refresh_access_token(self, refresh_token_str: str, request: Request) -> TokenResponse:
        """
        Refresh access token using refresh token
        """
        # Verify refresh token
        try:
            payload = verify_token(refresh_token_str, "refresh")
        except CustomHTTPException:
            raise CustomHTTPException(
                status_code=401,
                detail="Invalid refresh token",
                error_code="INVALID_REFRESH_TOKEN"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise CustomHTTPException(
                status_code=401,
                detail="Invalid refresh token",
                error_code="INVALID_REFRESH_TOKEN"
            )
        
        # Check if refresh token exists and is valid
        refresh_token = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token == refresh_token_str)
            .filter(RefreshToken.user_id == int(user_id))
            .first()
        )
        
        if not refresh_token or not refresh_token.is_valid:
            raise CustomHTTPException(
                status_code=401,
                detail="Invalid or expired refresh token",
                error_code="INVALID_REFRESH_TOKEN"
            )
        
        # Get user
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise CustomHTTPException(
                status_code=401,
                detail="User not found or disabled",
                error_code="USER_NOT_FOUND"
            )
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        
        logger.info(f"Access token refreshed for user: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_verified": user.is_verified
            }
        )
    
    def logout_user(self, refresh_token_str: str) -> bool:
        """
        Logout user by revoking refresh token
        """
        refresh_token = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token == refresh_token_str)
            .first()
        )
        
        if refresh_token:
            refresh_token.revoke()
            self.db.commit()
            logger.info(f"User logged out, token revoked: {refresh_token.user.email}")
            return True
        
        return False
    
    def logout_all_devices(self, user_id: int) -> int:
        """
        Logout user from all devices by revoking all refresh tokens
        """
        tokens = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id)
            .filter(RefreshToken.is_active == True)
            .filter(RefreshToken.is_revoked == False)
            .all()
        )
        
        count = 0
        for token in tokens:
            token.revoke()
            count += 1
        
        self.db.commit()
        logger.info(f"User logged out from {count} devices")
        return count
    
    def send_email_verification(self, email: str, request: Request) -> bool:
        """
        Send email verification to user
        """
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise CustomHTTPException(
                status_code=404,
                detail="User not found",
                error_code="USER_NOT_FOUND"
            )
        
        if user.is_verified:
            raise CustomHTTPException(
                status_code=400,
                detail="Email already verified",
                error_code="EMAIL_ALREADY_VERIFIED"
            )
        
        return self._send_email_verification(user, request)
    
    def verify_email(self, token: str) -> bool:
        """
        Verify user email using token
        """
        # Verify token
        try:
            payload = verify_token(token, "email_verification")
        except CustomHTTPException:
            raise CustomHTTPException(
                status_code=400,
                detail="Invalid or expired verification token",
                error_code="INVALID_VERIFICATION_TOKEN"
            )
        
        email = payload.get("email")
        if not email:
            raise CustomHTTPException(
                status_code=400,
                detail="Invalid verification token",
                error_code="INVALID_VERIFICATION_TOKEN"
            )
        
        # Find user and update verification status
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise CustomHTTPException(
                status_code=404,
                detail="User not found",
                error_code="USER_NOT_FOUND"
            )
        
        if user.is_verified:
            raise CustomHTTPException(
                status_code=400,
                detail="Email already verified",
                error_code="EMAIL_ALREADY_VERIFIED"
            )
        
        user.is_verified = True
        user.email_verified_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Email verified successfully: {user.email}")
        return True
    
    def send_password_reset(self, email: str, request: Request) -> bool:
        """
        Send password reset email
        """
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if user exists or not
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return True
        
        if not user.is_active:
            logger.warning(f"Password reset requested for inactive user: {email}")
            return True
        
        return self._send_password_reset(user, request)
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset user password using token
        """
        # Verify token
        try:
            payload = verify_token(token, "password_reset")
        except CustomHTTPException:
            raise CustomHTTPException(
                status_code=400,
                detail="Invalid or expired reset token",
                error_code="INVALID_RESET_TOKEN"
            )
        
        email = payload.get("email")
        if not email:
            raise CustomHTTPException(
                status_code=400,
                detail="Invalid reset token",
                error_code="INVALID_RESET_TOKEN"
            )
        
        # Find user and update password
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise CustomHTTPException(
                status_code=404,
                detail="User not found",
                error_code="USER_NOT_FOUND"
            )
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        user.password_reset_at = datetime.utcnow()
        
        # Revoke all refresh tokens for security
        refresh_tokens = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.user_id == user.id)
            .filter(RefreshToken.is_active == True)
            .all()
        )
        
        for refresh_token in refresh_tokens:
            refresh_token.revoke()
        
        self.db.commit()
        
        logger.info(f"Password reset successfully: {user.email}")
        return True
    
    def _send_email_verification(self, user: User, request: Request) -> bool:
        """
        Internal method to send email verification
        """
        # Create verification token
        verification_token = create_email_verification_token(user.email)
        
        # Store token in database
        db_token = EmailVerificationToken(
            token=verification_token,
            user_id=user.id
        )
        self.db.add(db_token)
        self.db.commit()
        
        # Send email
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
        try:
            self.email_service.send_email_verification(
                email=user.email,
                full_name=user.full_name or user.email,
                verification_url=verification_url
            )
            logger.info(f"Email verification sent to: {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email verification: {str(e)}")
            raise CustomHTTPException(
                status_code=500,
                detail="Failed to send verification email",
                error_code="EMAIL_SEND_FAILED"
            )
    
    def _send_password_reset(self, user: User, request: Request) -> bool:
        """
        Internal method to send password reset email
        """
        # Create reset token
        reset_token = create_password_reset_token(user.email)
        
        # Store token in database
        db_token = PasswordResetToken(
            token=reset_token,
            user_id=user.id,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent")
        )
        self.db.add(db_token)
        self.db.commit()
        
        # Send email
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        try:
            self.email_service.send_password_reset(
                email=user.email,
                full_name=user.full_name or user.email,
                reset_url=reset_url
            )
            logger.info(f"Password reset email sent to: {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            raise CustomHTTPException(
                status_code=500,
                detail="Failed to send reset email",
                error_code="EMAIL_SEND_FAILED"
            )

    def reset_password_direct(self, email: str, new_password: str) -> bool:
        """
        Reset password directly (for OTP-verified users)
        """
        # Find user
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise CustomHTTPException(
                status_code=404,
                detail="User not found",
                error_code="USER_NOT_FOUND"
            )
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        user.password_reset_at = datetime.utcnow()
        
        # Revoke all refresh tokens for security
        refresh_tokens = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.user_id == user.id)
            .filter(RefreshToken.is_active == True)
            .all()
        )
        
        for refresh_token in refresh_tokens:
            refresh_token.revoke()
        
        self.db.commit()
        
        logger.info(f"Password reset successfully (OTP verified): {user.email}")
        return True
