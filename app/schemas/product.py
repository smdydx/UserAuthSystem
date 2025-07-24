"""
Product-related Pydantic schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from app.models.product import ProductStatus, DiscountType
import re


class ProductImageBase(BaseModel):
    """Base product image schema"""
    url: str
    alt_text: Optional[str] = None
    sort_order: int = 0
    is_primary: bool = False


class ProductImageCreate(ProductImageBase):
    """Schema for creating product image"""
    filename: Optional[str] = None
    size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ProductImageResponse(ProductImageBase):
    """Schema for product image response"""
    id: int
    filename: Optional[str]
    size: Optional[int]
    width: Optional[int]
    height: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class VariantOptionBase(BaseModel):
    """Base variant option schema"""
    name: str = Field(..., max_length=50)
    value: str = Field(..., max_length=100)
    display_value: Optional[str] = Field(None, max_length=100)
    color_code: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class VariantOptionCreate(VariantOptionBase):
    """Schema for creating variant option"""
    pass


class VariantOptionResponse(VariantOptionBase):
    """Schema for variant option response"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductVariantBase(BaseModel):
    """Base product variant schema"""
    sku: str = Field(..., max_length=100)
    title: Optional[str] = Field(None, max_length=200)
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    inventory_quantity: int = 0
    weight: Optional[Decimal] = None
    options: Optional[Dict[str, str]] = {}
    is_active: bool = True
    image_url: Optional[str] = None


class ProductVariantCreate(ProductVariantBase):
    """Schema for creating product variant"""
    pass


class ProductVariantUpdate(BaseModel):
    """Schema for updating product variant"""
    sku: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=200)
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    inventory_quantity: Optional[int] = None
    weight: Optional[Decimal] = None
    options: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None


class ProductVariantResponse(ProductVariantBase):
    """Schema for product variant response"""
    id: int
    product_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ProductDiscountBase(BaseModel):
    """Base product discount schema"""
    name: str = Field(..., max_length=100)
    discount_type: DiscountType
    value: Decimal = Field(..., gt=0)
    min_quantity: int = Field(1, ge=1)
    min_amount: Optional[Decimal] = None
    is_active: bool = True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    usage_limit: Optional[int] = None


class ProductDiscountCreate(ProductDiscountBase):
    """Schema for creating product discount"""
    
    @validator('ends_at')
    def validate_end_date(cls, v, values):
        if v and values.get('starts_at') and v <= values['starts_at']:
            raise ValueError('End date must be after start date')
        return v


class ProductDiscountUpdate(BaseModel):
    """Schema for updating product discount"""
    name: Optional[str] = Field(None, max_length=100)
    discount_type: Optional[DiscountType] = None
    value: Optional[Decimal] = Field(None, gt=0)
    min_quantity: Optional[int] = Field(None, ge=1)
    min_amount: Optional[Decimal] = None
    is_active: Optional[bool] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    usage_limit: Optional[int] = None


class ProductDiscountResponse(ProductDiscountBase):
    """Schema for product discount response"""
    id: int
    product_id: int
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., min_length=1, max_length=200)
    short_description: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    compare_at_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    track_inventory: bool = True
    inventory_quantity: int = 0
    low_stock_threshold: int = 10
    weight: Optional[Decimal] = None
    dimensions: Optional[Dict[str, float]] = None  # {"length": 10, "width": 5, "height": 3}
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=300)
    status: ProductStatus = ProductStatus.DRAFT
    is_featured: bool = False
    is_digital: bool = False
    requires_shipping: bool = True
    category_id: Optional[int] = None


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    sku: str = Field(..., max_length=100)
    slug: Optional[str] = Field(None, max_length=220)
    tag_ids: Optional[List[int]] = []
    images: Optional[List[ProductImageCreate]] = []
    variants: Optional[List[ProductVariantCreate]] = []
    discounts: Optional[List[ProductDiscountCreate]] = []
    
    @validator('slug')
    def validate_slug(cls, v, values):
        if v is None:
            # Generate slug from name
            name = values.get('name', '')
            v = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
            v = re.sub(r'\s+', '-', v.strip())
        return v
    
    @validator('compare_at_price')
    def validate_compare_price(cls, v, values):
        if v is not None and values.get('price') and v <= values['price']:
            raise ValueError('Compare at price must be greater than price')
        return v


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, max_length=220)
    sku: Optional[str] = Field(None, max_length=100)
    short_description: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    compare_at_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    track_inventory: Optional[bool] = None
    inventory_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    weight: Optional[Decimal] = None
    dimensions: Optional[Dict[str, float]] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=300)
    status: Optional[ProductStatus] = None
    is_featured: Optional[bool] = None
    is_digital: Optional[bool] = None
    requires_shipping: Optional[bool] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None


class ProductSummary(BaseModel):
    """Schema for product summary (used in lists)"""
    id: int
    name: str
    slug: str
    sku: str
    price: Decimal
    compare_at_price: Optional[Decimal]
    status: ProductStatus
    is_featured: bool
    inventory_quantity: int
    primary_image: Optional[str] = None
    category_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductResponse(ProductBase):
    """Schema for detailed product response"""
    id: int
    slug: str
    sku: str
    created_at: datetime
    updated_at: Optional[datetime]
    published_at: Optional[datetime]
    
    # Related data
    category: Optional[dict] = None
    images: List[ProductImageResponse] = []
    variants: List[ProductVariantResponse] = []
    tags: List[dict] = []
    discounts: List[ProductDiscountResponse] = []
    
    # Calculated fields
    has_variants: bool = False
    is_on_sale: bool = False
    discount_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for paginated product list"""
    items: List[ProductSummary]
    total: int
    page: int
    size: int
    pages: int


class ProductSearchFilters(BaseModel):
    """Schema for product search filters"""
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    status: Optional[ProductStatus] = None
    is_featured: Optional[bool] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    in_stock: Optional[bool] = None
    search: Optional[str] = None


# Forward reference resolution will be handled when needed