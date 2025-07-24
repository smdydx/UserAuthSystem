"""
Database models package
"""
from app.models.user import User, UserRole
from app.models.token import RefreshToken, EmailVerificationToken, PasswordResetToken
from app.models.otp import OTPVerification
from app.models.category import Category, ProductTag
from app.models.product import (
    Product, ProductImage, ProductVariant, VariantOption, 
    ProductDiscount, ProductStatus, DiscountType,
    product_tag_associations
)

__all__ = [
    "User",
    "UserRole", 
    "RefreshToken",
    "EmailVerificationToken",
    "PasswordResetToken",
    "OTPVerification",
    "Category", 
    "ProductTag",
    "Product", 
    "ProductImage", 
    "ProductVariant", 
    "VariantOption",
    "ProductDiscount", 
    "ProductStatus", 
    "DiscountType",
    "product_tag_associations"
]
