"""
Category-related Pydantic schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
import re


class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=300)
    image_url: Optional[str] = None
    is_active: bool = True
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    """Schema for creating a category"""
    slug: Optional[str] = Field(None, max_length=120)
    
    @validator('slug')
    def validate_slug(cls, v, values):
        if v is None:
            # Generate slug from name
            name = values.get('name', '')
            v = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
            v = re.sub(r'\s+', '-', v.strip())
        return v


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=300)
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    parent_id: Optional[int] = None


class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: int
    slug: str
    created_at: datetime
    updated_at: Optional[datetime]
    subcategories: List['CategoryResponse'] = []
    product_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ProductTagBase(BaseModel):
    """Base product tag schema"""
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field("#007bff", pattern=r'^#[0-9A-Fa-f]{6}$')


class ProductTagCreate(ProductTagBase):
    """Schema for creating a product tag"""
    slug: Optional[str] = Field(None, max_length=60)
    
    @validator('slug')
    def validate_slug(cls, v, values):
        if v is None:
            # Generate slug from name
            name = values.get('name', '')
            v = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
            v = re.sub(r'\s+', '-', v.strip())
        return v


class ProductTagUpdate(BaseModel):
    """Schema for updating a product tag"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    slug: Optional[str] = Field(None, max_length=60)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class ProductTagResponse(ProductTagBase):
    """Schema for product tag response"""
    id: int
    slug: str
    created_at: datetime
    product_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# Forward reference resolution will be handled when needed
CategoryResponse.model_rebuild()