"""
Product API routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session
import math

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.product import ProductStatus
from app.services.product_service import ProductService, ProductImageService
from app.services.variant_service import ProductVariantService, VariantOptionService
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductSummary,
    ProductListResponse, ProductSearchFilters, ProductImageCreate,
    ProductVariantCreate, ProductVariantUpdate, ProductVariantResponse,
    VariantOptionCreate, VariantOptionResponse
)

router = APIRouter()

# ===============================
# PRODUCT ENDPOINTS
# ===============================

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new product (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create products"
        )
    
    return ProductService.create_product(db, product_data)


@router.get("/products", response_model=ProductListResponse)
async def get_products(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    tag_ids: Optional[str] = Query(None, description="Comma-separated tag IDs"),
    status: Optional[ProductStatus] = Query(None),
    is_featured: Optional[bool] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at", pattern="^(name|price|created_at|updated_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """Get products with pagination and filters"""
    # Parse tag_ids if provided
    parsed_tag_ids = None
    if tag_ids:
        try:
            parsed_tag_ids = [int(id.strip()) for id in tag_ids.split(',') if id.strip()]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tag_ids format"
            )
    
    # Create filters
    filters = ProductSearchFilters(
        category_id=category_id,
        tag_ids=parsed_tag_ids,
        status=status,
        is_featured=is_featured,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        search=search
    )
    
    # Calculate skip
    skip = (page - 1) * size
    
    # Get products
    products, total = ProductService.get_products(
        db, skip=skip, limit=size, filters=filters, 
        sort_by=sort_by, sort_order=sort_order
    )
    
    # Calculate pagination
    pages = math.ceil(total / size) if total > 0 else 1
    
    return ProductListResponse(
        items=[ProductSummary.from_orm(p) for p in products],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/products/featured", response_model=List[ProductSummary])
async def get_featured_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get featured products"""
    products = ProductService.get_featured_products(db, limit=limit)
    return [ProductSummary.from_orm(p) for p in products]


@router.get("/products/search", response_model=List[ProductSummary])
async def search_products(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search products by name, description, or SKU"""
    products = ProductService.search_products(db, q, skip=skip, limit=limit)
    return [ProductSummary.from_orm(p) for p in products]


@router.get("/products/category/{category_id}", response_model=List[ProductSummary])
async def get_products_by_category(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get products by category"""
    products = ProductService.get_products_by_category(
        db, category_id, skip=skip, limit=limit
    )
    return [ProductSummary.from_orm(p) for p in products]


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get product by ID"""
    product = ProductService.get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.get("/products/slug/{slug}", response_model=ProductResponse)
async def get_product_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get product by slug"""
    product = ProductService.get_product(db, slug=slug)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update product (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update products"
        )
    
    product = ProductService.update_product(db, product_id, product_data)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete product (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete products"
        )
    
    if not ProductService.delete_product(db, product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )


# ===============================
# PRODUCT IMAGE ENDPOINTS
# ===============================

@router.post("/products/{product_id}/images", status_code=status.HTTP_201_CREATED)
async def add_product_image(
    product_id: int,
    image_data: ProductImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add image to product (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can add product images"
        )
    
    return ProductImageService.add_product_image(db, product_id, image_data)


@router.delete("/products/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete product image (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete product images"
        )
    
    if not ProductImageService.delete_product_image(db, image_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )


@router.put("/products/{product_id}/images/{image_id}/primary", status_code=status.HTTP_200_OK)
async def set_primary_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Set image as primary for product (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can set primary images"
        )
    
    if not ProductImageService.set_primary_image(db, product_id, image_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    return {"message": "Primary image updated successfully"}


# ===============================
# PRODUCT VARIANT ENDPOINTS
# ===============================

@router.post("/products/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_product_variant(
    product_id: int,
    variant_data: ProductVariantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create product variant (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create variants"
        )
    
    return ProductVariantService.create_variant(db, product_id, variant_data)


@router.get("/products/{product_id}/variants", response_model=List[ProductVariantResponse])
async def get_product_variants(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get all variants for a product"""
    return ProductVariantService.get_product_variants(db, product_id)


@router.get("/variants/{variant_id}", response_model=ProductVariantResponse)
async def get_variant(
    variant_id: int,
    db: Session = Depends(get_db)
):
    """Get variant by ID"""
    variant = ProductVariantService.get_variant(db, variant_id)
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found"
        )
    return variant


@router.put("/variants/{variant_id}", response_model=ProductVariantResponse)
async def update_variant(
    variant_id: int,
    variant_data: ProductVariantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update product variant (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update variants"
        )
    
    variant = ProductVariantService.update_variant(db, variant_id, variant_data)
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found"
        )
    return variant


@router.put("/variants/{variant_id}/inventory", response_model=ProductVariantResponse)
async def update_variant_inventory(
    variant_id: int,
    quantity: int = Query(..., ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update variant inventory (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update inventory"
        )
    
    variant = ProductVariantService.update_variant_inventory(db, variant_id, quantity)
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found"
        )
    return variant


@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    variant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete product variant (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete variants"
        )
    
    if not ProductVariantService.delete_variant(db, variant_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found"
        )


# ===============================
# VARIANT OPTION ENDPOINTS
# ===============================

@router.post("/variant-options", response_model=VariantOptionResponse, status_code=status.HTTP_201_CREATED)
async def create_variant_option(
    option_data: VariantOptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create variant option (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create variant options"
        )
    
    return VariantOptionService.create_option(db, option_data)


@router.get("/variant-options", response_model=List[VariantOptionResponse])
async def get_variant_options(
    option_name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get variant options, optionally filtered by name"""
    return VariantOptionService.get_options(db, option_name=option_name)


@router.get("/variant-options/names", response_model=List[str])
async def get_variant_option_names(db: Session = Depends(get_db)):
    """Get unique variant option names (e.g., Color, Size)"""
    return VariantOptionService.get_option_names(db)


@router.delete("/variant-options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant_option(
    option_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete variant option (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete variant options"
        )
    
    if not VariantOptionService.delete_option(db, option_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant option not found"
        )