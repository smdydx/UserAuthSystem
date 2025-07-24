"""
Category and Subcategory Models
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Category(Base):
    """Product category model"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # SEO fields
    meta_title = Column(String(200))
    meta_description = Column(String(500))
    meta_keywords = Column(String(300))
    
    # Image
    image_url = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Parent category for subcategories
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category")


class ProductTag(Base):
    """Product tags for better organization"""
    __tablename__ = "product_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    slug = Column(String(60), unique=True, nullable=False, index=True)
    color = Column(String(7), default="#007bff")  # Hex color code
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships - Many-to-many with products
    products = relationship("Product", secondary="product_tag_associations", back_populates="tags")