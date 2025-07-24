"""
Email service for sending various types of emails
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import ssl

from app.core.config import settings
from app.utils.exceptions import CustomHTTPException

logger = logging.getLogger(__name__)


class EmailService:
    """Email service class for sending emails"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Internal method to send email
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Create SMTP session
            context = ssl.create_default_context()
            
            # Connect to server and send email
            if self.smtp_username and self.smtp_password:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(message)
            else:
                # For local development or when credentials are not provided
                logger.warning("SMTP credentials not provided, email sending skipped")
                print(f"Email would be sent to: {to_email}")
                print(f"Subject: {subject}")
                print(f"Content: {html_content}")
                return True
            
            logger.info(f"Email sent successfully to: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise CustomHTTPException(
                status_code=500,
                detail=f"Failed to send email: {str(e)}",
                error_code="EMAIL_SEND_FAILED"
            )
    
    def send_email_verification(self, email: str, full_name: str, verification_url: str) -> bool:
        """
        Send email verification email
        """
        subject = "Verify your email address"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f8f9fa; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #007bff; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Email Verification</h1>
                </div>
                <div class="content">
                    <h2>Hello {full_name},</h2>
                    <p>Thank you for registering with our service. To complete your registration, please verify your email address by clicking the button below:</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </div>
                    
                    <p>If the button doesn't work, you can also copy and paste the following link into your browser:</p>
                    <p style="word-break: break-all; color: #007bff;">{verification_url}</p>
                    
                    <p><strong>Note:</strong> This verification link will expire in {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours.</p>
                    
                    <p>If you didn't create an account with us, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 {settings.PROJECT_NAME}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hello {full_name},
        
        Thank you for registering with our service. To complete your registration, please verify your email address by visiting:
        
        {verification_url}
        
        This verification link will expire in {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours.
        
        If you didn't create an account with us, please ignore this email.
        
        © 2025 {settings.PROJECT_NAME}. All rights reserved.
        """
        
        return self._send_email(email, subject, html_content, text_content)
    
    def send_password_reset(self, email: str, full_name: str, reset_url: str) -> bool:
        """
        Send password reset email
        """
        subject = "Reset your password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f8f9fa; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #dc3545; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 14px; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset</h1>
                </div>
                <div class="content">
                    <h2>Hello {full_name},</h2>
                    <p>We received a request to reset your password. If you made this request, click the button below to reset your password:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </div>
                    
                    <p>If the button doesn't work, you can also copy and paste the following link into your browser:</p>
                    <p style="word-break: break-all; color: #dc3545;">{reset_url}</p>
                    
                    <div class="warning">
                        <p><strong>Security Notice:</strong></p>
                        <ul>
                            <li>This password reset link will expire in {settings.PASSWORD_RESET_EXPIRE_HOURS} hour(s)</li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>For security, all active sessions will be logged out after password reset</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>© 2025 {settings.PROJECT_NAME}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hello {full_name},
        
        We received a request to reset your password. If you made this request, visit the following link to reset your password:
        
        {reset_url}
        
        This password reset link will expire in {settings.PASSWORD_RESET_EXPIRE_HOURS} hour(s).
        
        If you didn't request this reset, please ignore this email.
        
        For security, all active sessions will be logged out after password reset.
        
        © 2025 {settings.PROJECT_NAME}. All rights reserved.
        """
        
        return self._send_email(email, subject, html_content, text_content)
    
    def send_welcome_email(self, email: str, full_name: str) -> bool:
        """
        Send welcome email after successful registration and verification
        """
        subject = f"Welcome to {settings.PROJECT_NAME}!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f8f9fa; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {settings.PROJECT_NAME}!</h1>
                </div>
                <div class="content">
                    <h2>Hello {full_name},</h2>
                    <p>Congratulations! Your email has been successfully verified and your account is now active.</p>
                    
                    <p>You can now enjoy all the features of our platform. If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                    
                    <p>Thank you for joining us!</p>
                </div>
                <div class="footer">
                    <p>© 2025 {settings.PROJECT_NAME}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hello {full_name},
        
        Congratulations! Your email has been successfully verified and your account is now active.
        
        You can now enjoy all the features of our platform. If you have any questions or need assistance, please don't hesitate to contact our support team.
        
        Thank you for joining us!
        
        © 2025 {settings.PROJECT_NAME}. All rights reserved.
        """
        
        return self._send_email(email, subject, html_content, text_content)

    def send_password_reset_otp(self, email: str, full_name: str, otp_code: str) -> bool:
        """Send OTP for password reset verification"""
        subject = f"Password Reset OTP - {settings.PROJECT_NAME}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Password Reset OTP</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f8f9fa; }}
                .otp-box {{ 
                    background-color: #fff; border: 2px solid #dc3545; 
                    padding: 20px; text-align: center; border-radius: 10px; 
                    margin: 20px 0; font-size: 32px; font-weight: bold;
                    color: #dc3545; letter-spacing: 10px;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 14px; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset OTP</h1>
                </div>
                <div class="content">
                    <h2>Hello {full_name},</h2>
                    <p>Please use this OTP to reset your password:</p>
                    <div class="otp-box">{otp_code}</div>
                    <div class="warning">
                        <p><strong>Important:</strong></p>
                        <ul>
                            <li>Valid for <strong>10 minutes only</strong></li>
                            <li>You have <strong>3 attempts</strong></li>
                            <li>Do not share this OTP</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>© 2025 {settings.PROJECT_NAME}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hello {full_name},
        
        Your Password Reset OTP: {otp_code}
        
        Important:
        - Valid for 10 minutes only
        - You have 3 attempts
        - Do not share this OTP
        
        © 2025 {settings.PROJECT_NAME}. All rights reserved.
        """
        
        return self._send_email(email, subject, html_content, text_content)

    def send_order_confirmation(self, email: str, order_number: str, total: float, items: list) -> bool:
        """Send order confirmation email"""
        subject = f"Order Confirmation - {order_number}"
        
        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{item.product_name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{item.quantity}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">₹{item.final_price}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">₹{item.total_price}</td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Order Confirmation</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f8f9fa; }}
                .order-details {{ background-color: #fff; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .items-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .items-table th {{ background-color: #f8f9fa; padding: 10px; text-align: left; border-bottom: 2px solid #ddd; }}
                .total-row {{ font-weight: bold; background-color: #f8f9fa; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Order Confirmed!</h1>
                    <p>Order #{order_number}</p>
                </div>
                <div class="content">
                    <div class="order-details">
                        <h2>Order Details</h2>
                        <table class="items-table">
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th style="text-align: center;">Qty</th>
                                    <th style="text-align: right;">Price</th>
                                    <th style="text-align: right;">Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items_html}
                                <tr class="total-row">
                                    <td colspan="3" style="padding: 15px; text-align: right;">Grand Total:</td>
                                    <td style="padding: 15px; text-align: right;">₹{total}</td>
                                </tr>
                            </tbody>
                        </table>
                        <p><strong>We'll send you shipping confirmation once your order is on the way!</strong></p>
                    </div>
                </div>
                <div class="footer">
                    <p>© 2025 {settings.PROJECT_NAME}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, html_content)

    def send_order_status_update(self, email: str, order_number: str, status: str, tracking_number: str = None) -> bool:
        """Send order status update notification"""
        status_messages = {
            "confirmed": "Your order has been confirmed and is being prepared.",
            "processing": "Your order is being processed.",
            "shipped": "Great news! Your order has been shipped.",
            "delivered": "Your order has been delivered successfully.",
            "cancelled": "Your order has been cancelled.",
            "returned": "Your order return has been processed.",
            "refunded": "Your order refund has been processed."
        }
        
        subject = f"Order Update - {order_number}"
        message = status_messages.get(status, f"Your order status has been updated to {status}.")
        
        tracking_info = ""
        if tracking_number:
            tracking_info = f"""
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>📦 Tracking Information</h3>
                <p><strong>Tracking Number:</strong> {tracking_number}</p>
                <p>You can track your order using this number on our website.</p>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Order Status Update</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #17a2b8; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f8f9fa; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📋 Order Update</h1>
                    <p>Order #{order_number}</p>
                </div>
                <div class="content">
                    <h2>Status: {status.title()}</h2>
                    <p>{message}</p>
                    {tracking_info}
                </div>
                <div class="footer">
                    <p>© 2025 {settings.PROJECT_NAME}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, html_content)

    def send_refund_notification(self, email: str, order_number: str, refund_number: str, amount: float) -> bool:
        """Send refund notification email"""
        subject = f"Refund Processed - {refund_number}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Refund Notification</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f8f9fa; }}
                .refund-details {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💰 Refund Processed</h1>
                </div>
                <div class="content">
                    <div class="refund-details">
                        <h2>Refund Details</h2>
                        <p><strong>Order Number:</strong> {order_number}</p>
                        <p><strong>Refund Number:</strong> {refund_number}</p>
                        <p><strong>Refund Amount:</strong> ₹{amount}</p>
                    </div>
                    <p>Your refund has been processed and will reflect in your account within 5-7 business days.</p>
                    <p>If you have any questions, please contact our support team.</p>
                </div>
                <div class="footer">
                    <p>© 2025 {settings.PROJECT_NAME}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, html_content)
