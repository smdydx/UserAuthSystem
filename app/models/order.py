
"""
Order Management Models
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey, Numeric, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum
from datetime import datetime


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    RETURNED = "returned"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class Order(Base):
    """Order model"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # User information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for guest orders
    guest_email = Column(String(255), nullable=True)
    guest_phone = Column(String(20), nullable=True)
    
    # Order details
    status = Column(String(20), default=OrderStatus.PENDING, index=True)
    payment_status = Column(String(20), default=PaymentStatus.PENDING, index=True)
    
    # Pricing
    subtotal = Column(Numeric(10, 2), default=0.00)
    discount_amount = Column(Numeric(10, 2), default=0.00)
    tax_amount = Column(Numeric(10, 2), default=0.00)
    shipping_cost = Column(Numeric(10, 2), default=0.00)
    total = Column(Numeric(10, 2), nullable=False)
    
    # Addresses (JSON format for flexibility)
    billing_address = Column(JSON)  # Store complete address object
    shipping_address = Column(JSON)
    
    # Tracking & timestamps
    tracking_number = Column(String(100), nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Notes
    customer_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Metadata
    order_source = Column(String(50), default="web")  # web, mobile, admin
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")
    refunds = relationship("OrderRefund", back_populates="order", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_order_user_status', 'user_id', 'status'),
        Index('ix_order_created_status', 'created_at', 'status'),
    )
    
    @property
    def is_guest_order(self) -> bool:
        """Check if this is a guest order"""
        return self.user_id is None
    
    @property
    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]
    
    @property
    def can_be_refunded(self) -> bool:
        """Check if order can be refunded"""
        return self.status in [OrderStatus.DELIVERED] and self.payment_status == PaymentStatus.PAID


class OrderItem(Base):
    """Order item model"""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Product information (snapshot at time of order)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    
    # Product snapshot (for historical data)
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(100), nullable=True)
    variant_options = Column(JSON, nullable=True)  # Size, color, etc.
    
    # Pricing snapshot
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0.00)
    final_price = Column(Numeric(10, 2), nullable=False)
    
    # Quantity
    quantity = Column(Integer, nullable=False)
    
    # Custom options
    custom_options = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    
    @property
    def total_price(self) -> float:
        """Calculate total price for this item"""
        return float(self.final_price * self.quantity)


class OrderStatusHistory(Base):
    """Order status change history"""
    __tablename__ = "order_status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Status change details
    from_status = Column(String(20), nullable=True)
    to_status = Column(String(20), nullable=False)
    
    # Who made the change
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    changed_by_type = Column(String(20), default="admin")  # admin, system, customer
    
    # Additional information
    reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="status_history")
    changed_by = relationship("User")


class OrderRefund(Base):
    """Order refund model"""
    __tablename__ = "order_refunds"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Refund details
    refund_number = Column(String(50), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(255), nullable=False)
    
    # Status
    status = Column(String(20), default="pending")  # pending, approved, processed, rejected
    
    # Processing details
    processed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Notes
    customer_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="refunds")
    processed_by = relationship("User")


class OrderInventoryReservation(Base):
    """Inventory reservation for orders"""
    __tablename__ = "order_inventory_reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    
    # Reservation details
    quantity_reserved = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # Auto-release after X minutes
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    released_at = Column(DateTime, nullable=True)
    
    # Relationships
    product = relationship("Product")
    variant = relationship("ProductVariant")


class OrderNotification(Base):
    """Order notification log"""
    __tablename__ = "order_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Notification details
    notification_type = Column(String(50), nullable=False)  # email, sms
    recipient = Column(String(255), nullable=False)
    template_name = Column(String(100), nullable=False)
    
    # Status
    status = Column(String(20), default="pending")  # pending, sent, failed
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    order = relationship("Order")
