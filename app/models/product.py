"""
Product and related models
"""
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Integer, 
    ForeignKey, Numeric, JSON, Table, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from app.core.database import Base


# Association table for product-tag many-to-many relationship
product_tag_associations = Table(
    'product_tag_associations',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('product_tags.id'), primary_key=True)
)


class ProductStatus(str, Enum):
    """Product status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"


class DiscountType(str, Enum):
    """Discount type enumeration"""
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"


class Product(Base):
    """Main product model"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic product information
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(220), unique=True, nullable=False, index=True)
    short_description = Column(String(500))
    description = Column(Text)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    compare_at_price = Column(Numeric(10, 2))  # Original price for sale display
    cost_price = Column(Numeric(10, 2))  # Cost for profit calculations
    
    # Inventory
    track_inventory = Column(Boolean, default=True)
    inventory_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=10)
    
    # Physical properties
    weight = Column(Numeric(8, 2))  # in grams
    dimensions = Column(JSON)  # {"length": 10, "width": 5, "height": 3} in cm
    
    # SEO and marketing
    meta_title = Column(String(200))
    meta_description = Column(String(500))
    meta_keywords = Column(String(300))
    
    # Status and visibility
    status = Column(SQLEnum(ProductStatus), default=ProductStatus.DRAFT)
    is_featured = Column(Boolean, default=False)
    is_digital = Column(Boolean, default=False)
    requires_shipping = Column(Boolean, default=True)
    
    # Category relationship
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    
    # Relationships
    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    tags = relationship("ProductTag", secondary=product_tag_associations, back_populates="products")
    discounts = relationship("ProductDiscount", back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base):
    """Product images model"""
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Image details
    url = Column(String(500), nullable=False)
    alt_text = Column(String(200))
    sort_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)
    
    # Image metadata
    filename = Column(String(200))
    size = Column(Integer)  # Size in bytes
    width = Column(Integer)
    height = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="images")


class VariantOption(Base):
    """Variant options (e.g., Color: Red, Blue; Size: S, M, L)"""
    __tablename__ = "variant_options"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)  # e.g., "Color", "Size"
    value = Column(String(100), nullable=False)  # e.g., "Red", "Large"
    
    # Display
    display_value = Column(String(100))  # e.g., "Large (L)"
    color_code = Column(String(7))  # Hex color for color variants
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProductVariant(Base):
    """Product variants (combinations of options)"""
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Variant identification
    sku = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200))  # e.g., "Red / Large"
    
    # Pricing (optional override from main product)
    price = Column(Numeric(10, 2))
    compare_at_price = Column(Numeric(10, 2))
    cost_price = Column(Numeric(10, 2))
    
    # Inventory
    inventory_quantity = Column(Integer, default=0)
    
    # Physical properties (optional override)
    weight = Column(Numeric(8, 2))
    
    # Variant options as JSON
    options = Column(JSON)  # {"Color": "Red", "Size": "Large"}
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Images specific to this variant
    image_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="variants")


class ProductDiscount(Base):
    """Product discounts and pricing rules"""
    __tablename__ = "product_discounts"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Discount details
    name = Column(String(100), nullable=False)
    discount_type = Column(SQLEnum(DiscountType), nullable=False)
    value = Column(Numeric(10, 2), nullable=False)
    
    # Conditions
    min_quantity = Column(Integer, default=1)
    min_amount = Column(Numeric(10, 2))
    
    # Validity
    is_active = Column(Boolean, default=True)
    starts_at = Column(DateTime(timezone=True))
    ends_at = Column(DateTime(timezone=True))
    
    # Usage limits
    usage_limit = Column(Integer)  # Total usage limit
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="discounts")