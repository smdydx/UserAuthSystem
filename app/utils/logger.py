"""
Logging configuration and utilities
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        # Format the message
        return super().format(record)


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup application logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_file_size: Maximum log file size in bytes
        backup_count: Number of backup files to keep
    """
    
    # Determine log level
    if not log_level:
        log_level = settings.LOG_LEVEL
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log file is specified)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels for external libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)
    
    # Log initial message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, File: {log_file or 'Console only'}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class RequestLogger:
    """Logger for HTTP requests"""
    
    def __init__(self, name: str = "request"):
        self.logger = logging.getLogger(name)
    
    def log_request(self, method: str, url: str, status_code: int, 
                   duration: float, user_id: Optional[int] = None,
                   client_ip: Optional[str] = None):
        """
        Log HTTP request information
        
        Args:
            method: HTTP method
            url: Request URL
            status_code: Response status code
            duration: Request duration in seconds
            user_id: User ID (if authenticated)
            client_ip: Client IP address
        """
        user_info = f"user:{user_id}" if user_id else "anonymous"
        ip_info = f"ip:{client_ip}" if client_ip else "unknown"
        
        self.logger.info(
            f"{method} {url} - {status_code} - {duration:.3f}s - {user_info} - {ip_info}"
        )
    
    def log_error(self, method: str, url: str, error: str, 
                  user_id: Optional[int] = None, client_ip: Optional[str] = None):
        """
        Log HTTP request error
        
        Args:
            method: HTTP method
            url: Request URL
            error: Error message
            user_id: User ID (if authenticated)
            client_ip: Client IP address
        """
        user_info = f"user:{user_id}" if user_id else "anonymous"
        ip_info = f"ip:{client_ip}" if client_ip else "unknown"
        
        self.logger.error(
            f"{method} {url} - ERROR: {error} - {user_info} - {ip_info}"
        )


class SecurityLogger:
    """Logger for security events"""
    
    def __init__(self, name: str = "security"):
        self.logger = logging.getLogger(name)
    
    def log_login_attempt(self, email: str, success: bool, 
                         client_ip: Optional[str] = None, 
                         user_agent: Optional[str] = None):
        """Log login attempt"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"Login {status} - email:{email} - ip:{client_ip} - agent:{user_agent}"
        )
    
    def log_password_reset(self, email: str, client_ip: Optional[str] = None):
        """Log password reset request"""
        self.logger.info(f"Password reset requested - email:{email} - ip:{client_ip}")
    
    def log_email_verification(self, email: str, success: bool):
        """Log email verification attempt"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Email verification {status} - email:{email}")
    
    def log_suspicious_activity(self, description: str, user_id: Optional[int] = None,
                               client_ip: Optional[str] = None):
        """Log suspicious activity"""
        user_info = f"user:{user_id}" if user_id else "anonymous"
        self.logger.warning(
            f"Suspicious activity - {description} - {user_info} - ip:{client_ip}"
        )


# Global logger instances
request_logger = RequestLogger()
security_logger = SecurityLogger()
