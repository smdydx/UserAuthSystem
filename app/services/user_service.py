"""
User service for user management operations
"""
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User, UserRole
from app.schemas.user import UserUpdate, PasswordChangeRequest
from app.core.security import get_password_hash, verify_password
from app.utils.exceptions import CustomHTTPException

logger = logging.getLogger(__name__)


class UserService:
    """User service class for user management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(self, skip: int = 0, limit: int = 100, search: Optional[str] = None, role: Optional[UserRole] = None) -> List[User]:
        """
        Get list of users with optional filtering
        """
        query = self.db.query(User)
        
        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_filter),
                    User.full_name.ilike(search_filter)
                )
            )
        
        # Apply role filter
        if role:
            query = query.filter(User.role == role)
        
        return query.offset(skip).limit(limit).all()
    
    def count_users(self, search: Optional[str] = None, role: Optional[UserRole] = None) -> int:
        """Count users with optional filtering"""
        query = self.db.query(User)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_filter),
                    User.full_name.ilike(search_filter)
                )
            )
        
        if role:
            query = query.filter(User.role == role)
        
        return query.count()
    
    def update_user(self, user_id: int, user_update: UserUpdate, current_user: User) -> User:
        """
        Update user information
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise CustomHTTPException(
                status_code=404,
                detail="User not found",
                error_code="USER_NOT_FOUND"
            )
        
        # Check permissions
        if not self._can_update_user(current_user, user, user_update):
            raise CustomHTTPException(
                status_code=403,
                detail="Insufficient permissions",
                error_code="INSUFFICIENT_PERMISSIONS"
            )
        
        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        
        # Check if email is being changed and if it's already taken
        if "email" in update_data and update_data["email"] != user.email:
            existing_user = self.get_user_by_email(update_data["email"])
            if existing_user:
                raise CustomHTTPException(
                    status_code=400,
                    detail="Email already registered",
                    error_code="EMAIL_ALREADY_EXISTS"
                )
            # Reset email verification if email is changed
            user.is_verified = False
            user.email_verified_at = None
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"User updated: {user.email} by {current_user.email}")
        return user
    
    def change_password(self, user_id: int, password_change: PasswordChangeRequest, current_user: User) -> bool:
        """
        Change user password
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise CustomHTTPException(
                status_code=404,
                detail="User not found",
                error_code="USER_NOT_FOUND"
            )
        
        # Check permissions (users can only change their own password, admins can change any)
        if user.id != current_user.id and not current_user.is_admin:
            raise CustomHTTPException(
                status_code=403,
                detail="Insufficient permissions",
                error_code="INSUFFICIENT_PERMISSIONS"
            )
        
        # Verify current password (only if user is changing their own password)
        if user.id == current_user.id:
            if not verify_password(password_change.current_password, user.hashed_password):
                raise CustomHTTPException(
                    status_code=400,
                    detail="Current password is incorrect",
                    error_code="INVALID_CURRENT_PASSWORD"
                )
        
        # Update password
        user.hashed_password = get_password_hash(password_change.new_password)
        user.updated_at = datetime.utcnow()
        
        # Revoke all refresh tokens for security
        from app.models.token import RefreshToken
        refresh_tokens = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.user_id == user.id)
            .filter(RefreshToken.is_active == True)
            .all()
        )
        
        for token in refresh_tokens:
            token.revoke()
        
        self.db.commit()
        
        logger.info(f"Password changed for user: {user.email}")
        return True
    
    def deactivate_user(self, user_id: int, current_user: User) -> User:
        """
        Deactivate user account
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise CustomHTTPException(
                status_code=404,
                detail="User not found",
                error_code="USER_NOT_FOUND"
            )
        
        # Check permissions
        if not current_user.is_admin:
            raise CustomHTTPException(
                status_code=403,
                detail="Only admins can deactivate users",
                error_code="INSUFFICIENT_PERMISSIONS"
            )
        
        # Prevent deactivating the last admin
        if user.is_admin:
            admin_count = self.db.query(User).filter(
                User.role == UserRole.ADMIN,
                User.is_active == True,
                User.id != user.id
            ).count()
            
            if admin_count == 0:
                raise CustomHTTPException(
                    status_code=400,
                    detail="Cannot deactivate the last admin",
                    error_code="CANNOT_DEACTIVATE_LAST_ADMIN"
                )
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # Revoke all refresh tokens
        from app.models.token import RefreshToken
        refresh_tokens = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.user_id == user.id)
            .filter(RefreshToken.is_active == True)
            .all()
        )
        
        for token in refresh_tokens:
            token.revoke()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"User deactivated: {user.email} by {current_user.email}")
        return user
    
    def activate_user(self, user_id: int, current_user: User) -> User:
        """
        Activate user account
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise CustomHTTPException(
                status_code=404,
                detail="User not found",
                error_code="USER_NOT_FOUND"
            )
        
        # Check permissions
        if not current_user.is_admin:
            raise CustomHTTPException(
                status_code=403,
                detail="Only admins can activate users",
                error_code="INSUFFICIENT_PERMISSIONS"
            )
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"User activated: {user.email} by {current_user.email}")
        return user
    
    def delete_user(self, user_id: int, current_user: User) -> bool:
        """
        Permanently delete user account
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise CustomHTTPException(
                status_code=404,
                detail="User not found",
                error_code="USER_NOT_FOUND"
            )
        
        # Check permissions
        if not current_user.is_admin:
            raise CustomHTTPException(
                status_code=403,
                detail="Only admins can delete users",
                error_code="INSUFFICIENT_PERMISSIONS"
            )
        
        # Prevent deleting the last admin
        if user.is_admin:
            admin_count = self.db.query(User).filter(
                User.role == UserRole.ADMIN,
                User.id != user.id
            ).count()
            
            if admin_count == 0:
                raise CustomHTTPException(
                    status_code=400,
                    detail="Cannot delete the last admin",
                    error_code="CANNOT_DELETE_LAST_ADMIN"
                )
        
        self.db.delete(user)
        self.db.commit()
        
        logger.info(f"User deleted: {user.email} by {current_user.email}")
        return True
    
    def _can_update_user(self, current_user: User, target_user: User, user_update: UserUpdate) -> bool:
        """
        Check if current user can update target user
        """
        # Admins can update any user
        if current_user.is_admin:
            return True
        
        # Users can only update themselves
        if current_user.id != target_user.id:
            return False
        
        # Users cannot change their own role or admin flags
        update_data = user_update.dict(exclude_unset=True)
        restricted_fields = {"role", "is_superuser", "is_active", "is_verified"}
        
        if any(field in update_data for field in restricted_fields):
            return False
        
        return True
    
    def get_user_statistics(self) -> dict:
        """
        Get user statistics for admin dashboard
        """
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        verified_users = self.db.query(User).filter(User.is_verified == True).count()
        
        # Count by role
        role_counts = {}
        for role in UserRole:
            count = self.db.query(User).filter(User.role == role).count()
            role_counts[role.value] = count
        
        # Recent registrations (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_registrations = (
            self.db.query(User)
            .filter(User.created_at >= thirty_days_ago)
            .count()
        )
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "role_counts": role_counts,
            "recent_registrations": recent_registrations
        }
