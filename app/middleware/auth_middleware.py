"""
Authentication middleware for JWT token processing
"""
import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import verify_token
from app.models.user import User
from app.utils.exceptions import CustomHTTPException

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware to process JWT tokens and set current user
    """
    
    # Routes that don't require authentication
    EXEMPT_ROUTES = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/verify-email",
        "/api/v1/auth/send-verification-email",
        "/api/v1/auth/send-reset-otp",
        "/api/v1/auth/reset-password-otp",
        "/api/v1/auth/health"
    }
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and handle authentication
        """
        # Skip authentication for exempt routes
        if request.url.path in self.EXEMPT_ROUTES:
            return await call_next(request)
        
        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Extract and verify token
        current_user = await self._get_current_user(request)
        
        # Add current user to request state
        request.state.current_user = current_user
        
        # Proceed with request
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Error in request processing: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "error_code": "INTERNAL_SERVER_ERROR"}
            )
    
    async def _get_current_user(self, request: Request) -> Optional[User]:
        """
        Extract and verify JWT token, return current user
        """
        try:
            # Get Authorization header
            authorization = request.headers.get("Authorization")
            if not authorization:
                return None
            
            # Extract token from Bearer scheme
            if not authorization.startswith("Bearer "):
                return None
            
            token = authorization.split(" ")[1]
            
            # Verify token
            try:
                payload = verify_token(token, "access")
            except CustomHTTPException:
                return None
            
            # Get user from database
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            db: Session = SessionLocal()
            try:
                user = db.query(User).filter(User.id == int(user_id)).first()
                
                if not user or not user.is_active:
                    return None
                
                return user
            finally:
                db.close()
                
        except Exception as e:
            logger.warning(f"Authentication error: {str(e)}")
            return None
    
    def _is_route_exempt(self, path: str) -> bool:
        """
        Check if route is exempt from authentication
        """
        # Exact match
        if path in self.EXEMPT_ROUTES:
            return True
        
        # Pattern matching for dynamic routes
        exempt_patterns = [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/static/",
            "/favicon.ico"
        ]
        
        for pattern in exempt_patterns:
            if path.startswith(pattern):
                return True
        
        return False
