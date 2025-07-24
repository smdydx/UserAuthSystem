"""
Cart Management Schemas
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal

from app.models.cart import CartStatus


class CartItemBase(BaseModel):
    """Base cart item schema"""
    product_id: int = Field(..., gt=0)
    variant_id: Optional[int] = Field(None, gt=0)
    quantity: int = Field(..., gt=0, le=999)
    custom_options: Optional[Dict[str, Any]] = None
    notes: Optional[str] = Field(None, max_length=500)


class CartItemCreate(CartItemBase):
    """Schema for adding item to cart"""
    pass


class CartItemUpdate(BaseModel):
    """Schema for updating cart item"""
    quantity: Optional[int] = Field(None, gt=0, le=999)
    custom_options: Optional[Dict[str, Any]] = None
    notes: Optional[str] = Field(None, max_length=500)


class CartItemResponse(CartItemBase):
    """Cart item response schema"""
    id: int
    cart_id: int
    unit_price: Decimal
    original_price: Optional[Decimal]
    discount_amount: Decimal
    total_price: Decimal
    product_snapshot: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Product details (populated from relationships)
    product: Optional[Dict[str, Any]] = None
    variant: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class CartBase(BaseModel):
    """Base cart schema"""
    session_token: Optional[str] = Field(None, max_length=255)
    guest_email: Optional[str] = Field(None, max_length=255)
    currency: str = Field("INR", max_length=3)


class CartCreate(CartBase):
    """Schema for creating cart"""
    pass


class CartUpdate(BaseModel):
    """Schema for updating cart"""
    guest_email: Optional[str] = Field(None, max_length=255)
    shipping_address: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None
    applied_coupons: Optional[List[str]] = None


class CartSummary(BaseModel):
    """Cart summary for quick display"""
    id: int
    items_count: int
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    currency: str
    last_activity: datetime

    class Config:
        from_attributes = True


class CartResponse(CartBase):
    """Full cart response schema"""
    id: int
    user_id: Optional[int]
    status: CartStatus
    items_count: int
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    applied_coupons: Optional[List[str]]
    shipping_address: Optional[Dict[str, Any]]
    billing_address: Optional[Dict[str, Any]]
    expires_at: Optional[datetime]
    last_activity: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Cart items
    items: List[CartItemResponse] = []

    class Config:
        from_attributes = True


class CartSyncRequest(BaseModel):
    """Schema for syncing anonymous cart with user account"""
    session_token: str = Field(..., max_length=255)
    merge_strategy: str = Field("merge", pattern="^(merge|replace)$")


class SavedItemBase(BaseModel):
    """Base saved item schema"""
    product_id: int = Field(..., gt=0)
    variant_id: Optional[int] = Field(None, gt=0)
    quantity: int = Field(1, gt=0, le=999)
    list_name: str = Field("wishlist", max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    is_public: bool = False


class SavedItemCreate(SavedItemBase):
    """Schema for saving item"""
    pass


class SavedItemUpdate(BaseModel):
    """Schema for updating saved item"""
    quantity: Optional[int] = Field(None, gt=0, le=999)
    notes: Optional[str] = Field(None, max_length=500)
    list_name: Optional[str] = Field(None, max_length=100)
    is_public: Optional[bool] = None


class SavedItemResponse(SavedItemBase):
    """Saved item response schema"""
    id: int
    user_id: int
    saved_price: Optional[Decimal]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Product details
    product: Optional[Dict[str, Any]] = None
    variant: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class BulkCartOperation(BaseModel):
    """Schema for bulk cart operations"""
    items: List[CartItemCreate] = Field(..., min_items=1, max_items=50)


class CartValidationResponse(BaseModel):
    """Cart validation response"""
    is_valid: bool
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    updated_items: List[CartItemResponse] = []


class CartCheckoutSummary(BaseModel):
    """Cart summary for checkout process"""
    cart_id: int
    items_count: int
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    shipping_total: Decimal = Field(default=0.00)
    total: Decimal
    currency: str
    estimated_delivery: Optional[str] = None
    available_payment_methods: List[str] = []
    
    # Validation flags
    has_out_of_stock_items: bool = False
    has_price_changes: bool = False
    requires_shipping: bool = True


class CartAnalytics(BaseModel):
    """Cart analytics data"""
    cart_id: int
    abandonment_score: float = Field(..., ge=0, le=1)
    time_in_cart: Dict[str, int]  # seconds by item
    price_sensitivity: Optional[Dict[str, float]] = None
    recommended_actions: List[str] = []