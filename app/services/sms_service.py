"""
SMS service using Twilio for sending OTP codes
"""
import os
import logging
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """SMS service for sending OTP codes via Twilio"""
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_phone = os.getenv("TWILIO_PHONE_NUMBER")
        
        if self.account_sid and self.auth_token and self.from_phone:
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
            logger.info("SMS service initialized with Twilio")
        else:
            self.client = None
            self.enabled = False
            logger.warning("SMS service disabled - Twilio credentials not provided")
    
    def send_otp_sms(self, phone_number: str, otp_code: str, full_name: str = "User") -> bool:
        """
        Send OTP via SMS using Twilio
        """
        if not self.enabled:
            logger.warning(f"SMS service disabled, OTP would be sent to: {phone_number}")
            print(f"SMS would be sent to: {phone_number}")
            print(f"OTP Code: {otp_code}")
            print(f"Message: Hello {full_name}, your password reset OTP is: {otp_code}. Valid for 10 minutes. Do not share this code.")
            return True
        
        try:
            message_body = f"Hello {full_name}, your password reset OTP is: {otp_code}. Valid for 10 minutes. Do not share this code."
            
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_phone,
                to=phone_number
            )
            
            logger.info(f"SMS OTP sent successfully to {phone_number}, SID: {message.sid}")
            return True
            
        except TwilioException as e:
            logger.error(f"Twilio error sending SMS to {phone_number}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error sending SMS to {phone_number}: {str(e)}")
            return False
    
    def send_security_alert_sms(self, phone_number: str, full_name: str = "User") -> bool:
        """
        Send security alert SMS for password reset
        """
        if not self.enabled:
            logger.warning(f"SMS service disabled, security alert would be sent to: {phone_number}")
            return True
        
        try:
            message_body = f"Hello {full_name}, your password was recently reset. If this wasn't you, please contact support immediately."
            
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_phone,
                to=phone_number
            )
            
            logger.info(f"Security alert SMS sent to {phone_number}, SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending security alert SMS to {phone_number}: {str(e)}")
            return False
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Basic phone number validation
        """
        # Remove all non-digit characters
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # Check if it's a valid length (10-15 digits)
        if len(clean_number) < 10 or len(clean_number) > 15:
            return False
        
        return True
    
    def format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number for Twilio (add +1 if needed)
        """
        # Remove all non-digit characters
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # Add country code if not present
        if len(clean_number) == 10:  # US number without country code
            return f"+1{clean_number}"
        elif len(clean_number) == 11 and clean_number.startswith('1'):  # US number with 1
            return f"+{clean_number}"
        else:
            return f"+{clean_number}"