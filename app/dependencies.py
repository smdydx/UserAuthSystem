"""
FastAPI dependencies for authentication and authorization
"""
from typing import List, Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.utils.exceptions import CustomHTTPException, AuthenticationError, AuthorizationError


def get_current_user(request: Request) -> User:
    """
    Get current authenticated user from request state
    
    This dependency retrieves the user that was set by the auth middleware
    """
    current_user = getattr(request.state, 'current_user', None)
    
    if not current_user:
        raise AuthenticationError(
            detail="Authentication required",
            error_code="AUTHENTICATION_REQUIRED"
        )
    
    return current_user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user
    
    Ensures the user is active (not deactivated)
    """
    if not current_user.is_active:
        raise AuthenticationError(
            detail="Account is disabled",
            error_code="ACCOUNT_DISABLED"
        )
    
    return current_user


def get_current_verified_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Get current verified user
    
    Ensures the user has verified their email address
    """
    if not current_user.is_verified:
        raise AuthenticationError(
            detail="Email verification required",
            error_code="EMAIL_NOT_VERIFIED"
        )
    
    return current_user


def require_role(allowed_roles: List[UserRole]):
    """
    Create a dependency that requires specific roles
    
    Args:
        allowed_roles: List of roles that are allowed to access the endpoint
    
    Returns:
        Dependency function
    """
    def check_role(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AuthorizationError(
                detail=f"Role {current_user.role.value} is not authorized. Required roles: {[role.value for role in allowed_roles]}",
                error_code="ROLE_REQUIRED"
            )
        return current_user
    
    return check_role


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require admin role
    
    Dependency that ensures the current user is an admin
    """
    if not current_user.is_admin:
        raise AuthorizationError(
            detail="Admin access required",
            error_code="ADMIN_REQUIRED"
        )
    
    return current_user


def require_admin_or_vendor(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require admin or vendor role
    
    Dependency that ensures the current user is either an admin or vendor
    """
    if not (current_user.is_admin or current_user.is_vendor):
        raise AuthorizationError(
            detail="Admin or vendor access required",
            error_code="ADMIN_OR_VENDOR_REQUIRED"
        )
    
    return current_user


def require_self_or_admin(user_id: int):
    """
    Create a dependency that requires the user to be accessing their own resource or be an admin
    
    Args:
        user_id: The ID of the user resource being accessed
    
    Returns:
        Dependency function
    """
    def check_self_or_admin(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.id != user_id and not current_user.is_admin:
            raise AuthorizationError(
                detail="You can only access your own resources or be an admin",
                error_code="SELF_OR_ADMIN_REQUIRED"
            )
        return current_user
    
    return check_self_or_admin


def get_optional_current_user(request: Request) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    
    This dependency doesn't raise an exception if the user is not authenticated
    """
    return getattr(request.state, 'current_user', None)


class RoleChecker:
    """
    Role checker class for more complex role-based access control
    """
    
    def __init__(self, allowed_roles: List[UserRole], require_verified: bool = False):
        self.allowed_roles = allowed_roles
        self.require_verified = require_verified
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        # Check if user has required role
        if current_user.role not in self.allowed_roles:
            raise AuthorizationError(
                detail=f"Access denied. Required roles: {[role.value for role in self.allowed_roles]}",
                error_code="INSUFFICIENT_ROLE"
            )
        
        # Check if email verification is required
        if self.require_verified and not current_user.is_verified:
            raise AuthenticationError(
                detail="Email verification required",
                error_code="EMAIL_NOT_VERIFIED"
            )
        
        return current_user


# Pre-defined role checkers
require_customer = RoleChecker([UserRole.CUSTOMER, UserRole.ADMIN, UserRole.VENDOR])
require_vendor = RoleChecker([UserRole.VENDOR, UserRole.ADMIN])
require_admin_only = RoleChecker([UserRole.ADMIN])

# Role checkers with email verification requirement
require_verified_customer = RoleChecker([UserRole.CUSTOMER, UserRole.ADMIN, UserRole.VENDOR], require_verified=True)
require_verified_vendor = RoleChecker([UserRole.VENDOR, UserRole.ADMIN], require_verified=True)
require_verified_admin = RoleChecker([UserRole.ADMIN], require_verified=True)


def get_pagination_params(
    page: int = 1,
    size: int = 10,
    max_size: int = 100
):
    """
    Get pagination parameters with validation
    
    Args:
        page: Page number (1-based)
        size: Page size
        max_size: Maximum allowed page size
    
    Returns:
        Tuple of (skip, limit) for database queries
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be >= 1"
        )
    
    if size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be >= 1"
        )
    
    if size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Page size must be <= {max_size}"
        )
    
    skip = (page - 1) * size
    limit = size
    
    return skip, limit
