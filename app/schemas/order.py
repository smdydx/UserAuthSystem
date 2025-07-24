
"""
Order Management Schemas
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
from decimal import Decimal

from app.models.order import OrderStatus, PaymentStatus


# Address Schema
class Address(BaseModel):
    """Address schema"""
    full_name: str
    phone: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "India"
    is_default: bool = False


# Order Creation Schemas
class OrderItemCreate(BaseModel):
    """Schema for creating order item"""
    product_id: int
    variant_id: Optional[int] = None
    quantity: int
    custom_options: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v


class OrderCreate(BaseModel):
    """Schema for creating order"""
    # Cart or items
    cart_id: Optional[int] = None
    items: Optional[List[OrderItemCreate]] = None
    
    # Customer details (for guest orders)
    guest_email: Optional[EmailStr] = None
    guest_phone: Optional[str] = None
    
    # Addresses
    billing_address: Address
    shipping_address: Optional[Address] = None  # If None, use billing address
    
    # Notes
    customer_notes: Optional[str] = None
    
    # Payment
    payment_method: str = "cod"  # cod, online, wallet
    
    @validator('items')
    def validate_items_or_cart(cls, v, values):
        cart_id = values.get('cart_id')
        if not cart_id and not v:
            raise ValueError('Either cart_id or items must be provided')
        if cart_id and v:
            raise ValueError('Provide either cart_id or items, not both')
        return v


# Order Response Schemas
class OrderItemResponse(BaseModel):
    """Order item response schema"""
    id: int
    product_id: int
    variant_id: Optional[int]
    product_name: str
    product_sku: Optional[str]
    variant_options: Optional[Dict[str, Any]]
    unit_price: Decimal
    discount_amount: Decimal
    final_price: Decimal
    quantity: int
    total_price: float
    custom_options: Optional[Dict[str, Any]]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class OrderStatusHistoryResponse(BaseModel):
    """Order status history response"""
    id: int
    from_status: Optional[str]
    to_status: str
    changed_by_type: str
    reason: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response schema"""
    id: int
    order_number: str
    user_id: Optional[int]
    guest_email: Optional[str]
    guest_phone: Optional[str]
    status: str
    payment_status: str
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    total: Decimal
    billing_address: Dict[str, Any]
    shipping_address: Dict[str, Any]
    tracking_number: Optional[str]
    customer_notes: Optional[str]
    order_source: str
    created_at: datetime
    updated_at: datetime
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    
    # Related data
    items: List[OrderItemResponse]
    status_history: Optional[List[OrderStatusHistoryResponse]] = None
    
    class Config:
        from_attributes = True


class OrderSummary(BaseModel):
    """Order summary for listing"""
    id: int
    order_number: str
    status: str
    payment_status: str
    total: Decimal
    items_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Order list response with pagination"""
    orders: List[OrderSummary]
    total: int
    page: int
    size: int
    pages: int


# Order Management Schemas
class OrderStatusUpdate(BaseModel):
    """Schema for updating order status"""
    status: OrderStatus
    reason: Optional[str] = None
    notes: Optional[str] = None
    tracking_number: Optional[str] = None


class OrderRefundCreate(BaseModel):
    """Schema for creating refund"""
    amount: Decimal
    reason: str
    customer_notes: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Refund amount must be greater than 0')
        return v


class OrderRefundResponse(BaseModel):
    """Order refund response"""
    id: int
    refund_number: str
    amount: Decimal
    reason: str
    status: str
    customer_notes: Optional[str]
    admin_notes: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Order Analytics Schemas
class OrderAnalytics(BaseModel):
    """Order analytics response"""
    total_orders: int
    total_revenue: Decimal
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    refunded_orders: int
    average_order_value: Decimal
    top_products: List[Dict[str, Any]]


# Order Search Filters
class OrderSearchFilters(BaseModel):
    """Order search and filtering"""
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    user_id: Optional[int] = None
    order_number: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
