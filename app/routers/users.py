"""
User management routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserUpdate, PasswordChangeRequest, UserProfile
from app.services.user_service import UserService
from app.dependencies import get_current_user, require_role, require_admin
from app.utils.exceptions import CustomHTTPException

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    search: Optional[str] = Query(None, description="Search users by email or name"),
    role: Optional[UserRole] = Query(None, description="Filter users by role"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get list of users (Admin only)
    
    - **skip**: Number of users to skip for pagination
    - **limit**: Maximum number of users to return
    - **search**: Search term for filtering by email or name
    - **role**: Filter by user role
    """
    user_service = UserService(db)
    try:
        users = user_service.get_users(skip=skip, limit=limit, search=search, role=role)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/statistics")
async def get_user_statistics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get user statistics (Admin only)
    
    Returns various statistics about users in the system
    """
    user_service = UserService(db)
    try:
        stats = user_service.get_user_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile
    
    Returns the profile information of the authenticated user
    """
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID
    
    - **user_id**: ID of the user to retrieve
    
    Users can only view their own profile unless they are admin
    """
    user_service = UserService(db)
    
    # Check if user can access this profile
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user information
    
    - **user_id**: ID of the user to update
    - **user_update**: Updated user information
    
    Users can only update their own profile (limited fields).
    Admins can update any user with full access.
    """
    user_service = UserService(db)
    try:
        updated_user = user_service.update_user(user_id, user_update, current_user)
        return updated_user
    except CustomHTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.post("/{user_id}/change-password")
async def change_password(
    user_id: int,
    password_change: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password
    
    - **user_id**: ID of the user whose password to change
    - **current_password**: Current password (required for own password change)
    - **new_password**: New password
    
    Users can only change their own password.
    Admins can change any user's password without knowing current password.
    """
    user_service = UserService(db)
    try:
        success = user_service.change_password(user_id, password_change, current_user)
        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )
    except CustomHTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Deactivate user account (Admin only)
    
    - **user_id**: ID of the user to deactivate
    
    Deactivated users cannot log in or access the system.
    """
    user_service = UserService(db)
    try:
        user = user_service.deactivate_user(user_id, current_user)
        return user
    except CustomHTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Activate user account (Admin only)
    
    - **user_id**: ID of the user to activate
    
    Activates a previously deactivated user account.
    """
    user_service = UserService(db)
    try:
        user = user_service.activate_user(user_id, current_user)
        return user
    except CustomHTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Permanently delete user account (Admin only)
    
    - **user_id**: ID of the user to delete
    
    WARNING: This action is irreversible!
    """
    user_service = UserService(db)
    try:
        success = user_service.delete_user(user_id, current_user)
        if success:
            return {"message": "User deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User deletion failed"
            )
    except CustomHTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


# Role-specific endpoints
@router.get("/admins/", response_model=List[UserResponse])
async def get_admin_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all admin users (Admin only)"""
    user_service = UserService(db)
    try:
        admins = user_service.get_users(role=UserRole.ADMIN)
        return admins
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin users"
        )


@router.get("/vendors/", response_model=List[UserResponse])
async def get_vendor_users(
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.VENDOR])),
    db: Session = Depends(get_db)
):
    """Get all vendor users (Admin and Vendor only)"""
    user_service = UserService(db)
    try:
        vendors = user_service.get_users(role=UserRole.VENDOR)
        return vendors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vendor users"
        )


@router.get("/customers/", response_model=List[UserResponse])
async def get_customer_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all customer users (Admin only)"""
    user_service = UserService(db)
    try:
        customers = user_service.get_users(role=UserRole.CUSTOMER)
        return customers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer users"
        )
