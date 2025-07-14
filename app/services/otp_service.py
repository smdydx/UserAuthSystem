"""
OTP service for generating and verifying OTPs
"""
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.otp import OTPVerification
from app.models.user import User
from app.utils.exceptions import CustomHTTPException
from app.services.email_service import EmailService
from app.services.sms_service import SMSService

logger = logging.getLogger(__name__)


class OTPService:
    """OTP service for password reset verification"""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
        self.sms_service = SMSService()
    
    def generate_otp(self, length: int = 6) -> str:
        """Generate random OTP code"""
        return ''.join(random.choices(string.digits, k=length))
    
    def send_password_reset_otp(self, email: str) -> bool:
        """
        Send OTP for password reset
        """
        # Find user
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if email exists - security best practice
            return True
        
        # Deactivate any existing OTPs
        existing_otps = (
            self.db.query(OTPVerification)
            .filter(OTPVerification.email == email)
            .filter(OTPVerification.is_used == False)
            .all()
        )
        
        for otp in existing_otps:
            otp.mark_as_used()
        
        # Generate new OTP
        otp_code = self.generate_otp()
        
        # Create OTP record
        otp_verification = OTPVerification(
            email=email,
            otp_code=otp_code,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(minutes=10)  # 10 minutes expiry
        )
        
        self.db.add(otp_verification)
        self.db.commit()
        
        # Send OTP via email
        try:
            self.email_service.send_password_reset_otp(
                email=email,
                full_name=user.full_name or user.email,
                otp_code=otp_code
            )
            logger.info(f"Password reset OTP sent to: {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send OTP email: {str(e)}")
            # Mark OTP as used since email failed
            otp_verification.mark_as_used()
            self.db.commit()
            raise CustomHTTPException(
                status_code=500,
                detail="Failed to send OTP email",
                error_code="EMAIL_SEND_FAILED"
            )
    
    def send_sms_otp(self, email: str, phone_number: str) -> bool:
        """
        Send OTP via SMS for password reset
        """
        # Find user
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if email exists - security best practice
            return True
        
        # Validate phone number
        if not self.sms_service.validate_phone_number(phone_number):
            raise CustomHTTPException(
                status_code=400,
                detail="Invalid phone number format",
                error_code="INVALID_PHONE_NUMBER"
            )
        
        # Update user's phone number if different
        formatted_phone = self.sms_service.format_phone_number(phone_number)
        if user.phone_number != formatted_phone:
            user.phone_number = formatted_phone
            self.db.commit()
        
        # Deactivate any existing OTPs
        existing_otps = (
            self.db.query(OTPVerification)
            .filter(OTPVerification.email == email)
            .filter(OTPVerification.is_used == False)
            .all()
        )
        
        for otp in existing_otps:
            otp.mark_as_used()
        
        # Generate new OTP
        otp_code = self.generate_otp()
        
        # Create OTP record
        otp_verification = OTPVerification(
            email=email,
            otp_code=otp_code,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(minutes=10)  # 10 minutes expiry
        )
        
        self.db.add(otp_verification)
        self.db.commit()
        
        # Send OTP via SMS
        try:
            success = self.sms_service.send_otp_sms(
                phone_number=formatted_phone,
                otp_code=otp_code,
                full_name=user.full_name or user.email
            )
            
            if success:
                logger.info(f"Password reset OTP sent via SMS to: {phone_number}")
                return True
            else:
                raise Exception("SMS service returned false")
                
        except Exception as e:
            logger.error(f"Failed to send OTP SMS: {str(e)}")
            # Mark OTP as used since SMS failed
            otp_verification.mark_as_used()
            self.db.commit()
            raise CustomHTTPException(
                status_code=500,
                detail="Failed to send OTP SMS",
                error_code="SMS_SEND_FAILED"
            )
    
    def verify_otp(self, email: str, otp_code: str) -> bool:
        """
        Verify OTP for password reset
        """
        # Find the latest valid OTP
        otp_verification = (
            self.db.query(OTPVerification)
            .filter(OTPVerification.email == email)
            .filter(OTPVerification.otp_code == otp_code)
            .filter(OTPVerification.is_used == False)
            .order_by(OTPVerification.created_at.desc())
            .first()
        )
        
        if not otp_verification:
            raise CustomHTTPException(
                status_code=400,
                detail="Invalid OTP code",
                error_code="INVALID_OTP"
            )
        
        # Check if OTP is expired
        if otp_verification.is_expired():
            raise CustomHTTPException(
                status_code=400,
                detail="OTP has expired",
                error_code="OTP_EXPIRED"
            )
        
        # Check attempts
        if otp_verification.attempts >= otp_verification.max_attempts:
            raise CustomHTTPException(
                status_code=400,
                detail="Maximum OTP attempts exceeded",
                error_code="OTP_ATTEMPTS_EXCEEDED"
            )
        
        # Increment attempts
        otp_verification.increment_attempts()
        
        # Verify OTP
        if otp_verification.otp_code == otp_code:
            otp_verification.verify()
            self.db.commit()
            logger.info(f"OTP verified successfully for: {email}")
            return True
        else:
            self.db.commit()
            raise CustomHTTPException(
                status_code=400,
                detail="Invalid OTP code",
                error_code="INVALID_OTP"
            )
    
    def is_otp_verified(self, email: str) -> bool:
        """
        Check if user has a verified OTP for password reset
        """
        otp_verification = (
            self.db.query(OTPVerification)
            .filter(OTPVerification.email == email)
            .filter(OTPVerification.is_verified == True)
            .filter(OTPVerification.is_used == False)
            .filter(OTPVerification.expires_at > datetime.utcnow())
            .order_by(OTPVerification.verified_at.desc())
            .first()
        )
        
        return otp_verification is not None
    
    def mark_otp_as_used(self, email: str) -> bool:
        """
        Mark verified OTP as used after password reset
        """
        otp_verification = (
            self.db.query(OTPVerification)
            .filter(OTPVerification.email == email)
            .filter(OTPVerification.is_verified == True)
            .filter(OTPVerification.is_used == False)
            .order_by(OTPVerification.verified_at.desc())
            .first()
        )
        
        if otp_verification:
            otp_verification.mark_as_used()
            self.db.commit()
            return True
        
        return False
    
    def cleanup_expired_otps(self) -> int:
        """
        Clean up expired OTPs (for maintenance)
        """
        expired_otps = (
            self.db.query(OTPVerification)
            .filter(OTPVerification.expires_at < datetime.utcnow())
            .all()
        )
        
        count = len(expired_otps)
        for otp in expired_otps:
            self.db.delete(otp)
        
        self.db.commit()
        logger.info(f"Cleaned up {count} expired OTPs")
        return count