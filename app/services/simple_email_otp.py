"""
Simple Email OTP Service - E-commerce Ready
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import ssl
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


class SimpleEmailOTP:
    """Simple email service for OTP sending"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = self.smtp_username or settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME
    
    def send_otp_email(self, to_email: str, otp_code: str, user_name: str = None) -> bool:
        """
        Send OTP via email - Simple format for e-commerce
        """
        if not self.smtp_username or not self.smtp_password:
            # For development - just log the OTP
            print(f"\n{'='*50}")
            print(f"📧 EMAIL OTP FOR: {to_email}")
            print(f"🔐 OTP CODE: {otp_code}")
            print(f"⏰ EXPIRES: 10 minutes")
            print(f"{'='*50}\n")
            return True
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Your OTP Code - {settings.PROJECT_NAME}"
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Simple HTML content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px;">
                    <div style="background-color: #007bff; color: white; padding: 20px; text-align: center;">
                        <h1>🔐 Your OTP Code</h1>
                    </div>
                    <div style="padding: 30px;">
                        <h2>Hello {user_name or 'User'},</h2>
                        <p>Your One-Time Password (OTP) for password reset is:</p>
                        <div style="background-color: #f8f9fa; border: 2px solid #007bff; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
                            <h1 style="color: #007bff; font-size: 36px; margin: 0; letter-spacing: 8px;">{otp_code}</h1>
                        </div>
                        <p><strong>Important:</strong></p>
                        <ul>
                            <li>Valid for <strong>10 minutes only</strong></li>
                            <li>Do not share this code with anyone</li>
                            <li>If you didn't request this, please ignore</li>
                        </ul>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 15px; text-align: center; color: #666;">
                        <p>© 2025 {settings.PROJECT_NAME}. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Simple text content
            text_content = f"""
            Your OTP Code - {settings.PROJECT_NAME}
            
            Hello {user_name or 'User'},
            
            Your One-Time Password (OTP) for password reset is: {otp_code}
            
            Important:
            - Valid for 10 minutes only
            - Do not share this code with anyone
            - If you didn't request this, please ignore
            
            © 2025 {settings.PROJECT_NAME}. All rights reserved.
            """
            
            # Add content to message
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"OTP email sent successfully to: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP email to {to_email}: {str(e)}")
            return False
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return bool(self.smtp_username and self.smtp_password)
    
    def get_config_instructions(self) -> str:
        """Get configuration instructions for Gmail"""
        return """
        To enable real email sending:
        1. Set SMTP_USERNAME=your.email@gmail.com
        2. Set SMTP_PASSWORD=your_app_password
        3. Create Gmail App Password: Google Account → Security → 2-factor auth → App passwords
        """