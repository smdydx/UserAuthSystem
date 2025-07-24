"""
Cart Management Models  
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey, Numeric, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum


class CartStatus(str, Enum):
    """Cart status enumeration"""
    ACTIVE = "active"
    ABANDONED = "abandoned"
    CONVERTED = "converted"
    EXPIRED = "expired"


class Cart(Base):
    """Shopping cart model"""
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    
    # User association (nullable for anonymous carts)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Anonymous cart identification
    session_token = Column(String(255), nullable=True, index=True)
    guest_email = Column(String(255), nullable=True)
    
    # Cart metadata
    status = Column(String(20), default=CartStatus.ACTIVE, index=True)
    currency = Column(String(3), default="INR")
    
    # Cart totals (calculated fields)
    items_count = Column(Integer, default=0)
    subtotal = Column(Numeric(10, 2), default=0.00)
    discount_total = Column(Numeric(10, 2), default=0.00)
    tax_total = Column(Numeric(10, 2), default=0.00)
    total = Column(Numeric(10, 2), default=0.00)
    
    # Applied discounts/coupons
    applied_coupons = Column(JSON)  # List of applied coupon codes
    
    # Shipping info (for guest checkout preparation)
    shipping_address = Column(JSON)
    billing_address = Column(JSON)
    
    # Cart persistence
    expires_at = Column(DateTime(timezone=True))  # For anonymous carts
    last_activity = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="carts")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_cart_user_status', 'user_id', 'status'),
        Index('idx_cart_session_status', 'session_token', 'status'),
        Index('idx_cart_expires', 'expires_at'),
    )


class CartItem(Base):
    """Cart item model"""
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False, index=True)
    
    # Product association
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True, index=True)
    
    # Item details
    quantity = Column(Integer, nullable=False, default=1)
    
    # Pricing snapshot (at time of adding to cart)
    unit_price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2))  # Before any discounts
    discount_amount = Column(Numeric(10, 2), default=0.00)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Product snapshot (in case product details change)
    product_snapshot = Column(JSON)  # Basic product info at time of adding
    
    # Custom options or notes
    custom_options = Column(JSON)  # Custom product options
    notes = Column(Text)  # Special instructions
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_cart_item_cart_product', 'cart_id', 'product_id'),
        Index('idx_cart_item_cart_variant', 'cart_id', 'variant_id'),
    )


class SavedItem(Base):
    """Saved for later / Wishlist items"""
    __tablename__ = "saved_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Product association
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    
    # Item details
    quantity = Column(Integer, default=1)
    notes = Column(Text)
    
    # Pricing snapshot
    saved_price = Column(Numeric(10, 2))  # Price when saved
    
    # Categories
    list_name = Column(String(100), default="wishlist")  # wishlist, favorites, etc.
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    
    # Unique constraint: user can save same product+variant only once per list
    __table_args__ = (
        Index('idx_saved_item_unique', 'user_id', 'product_id', 'variant_id', 'list_name', unique=True),
        Index('idx_saved_item_user_list', 'user_id', 'list_name'),
    )


class CartEvent(Base):
    """Cart activity tracking for analytics"""
    __tablename__ = "cart_events"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # add_item, remove_item, update_quantity, etc.
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    
    # Event data
    quantity_change = Column(Integer)  # +/- quantity change
    price_at_event = Column(Numeric(10, 2))
    event_data = Column(JSON)  # Additional event-specific data
    
    # Context
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    session_id = Column(String(255))
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    cart = relationship("Cart")
    user = relationship("User")
    product = relationship("Product")
    
    # Indexes for analytics
    __table_args__ = (
        Index('idx_cart_event_type_date', 'event_type', 'created_at'),
        Index('idx_cart_event_cart_date', 'cart_id', 'created_at'),
        Index('idx_cart_event_user_date', 'user_id', 'created_at'),
    )