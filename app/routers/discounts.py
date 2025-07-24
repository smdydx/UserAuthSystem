"""
Product discount API routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.services.discount_service import ProductDiscountService
from app.schemas.product import (
    ProductDiscountCreate, ProductDiscountUpdate, ProductDiscountResponse
)

router = APIRouter()

# ===============================
# PRODUCT DISCOUNT ENDPOINTS
# ===============================

@router.post("/products/{product_id}/discounts", response_model=ProductDiscountResponse, status_code=status.HTTP_201_CREATED)
async def create_product_discount(
    product_id: int,
    discount_data: ProductDiscountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new product discount (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create discounts"
        )
    
    return ProductDiscountService.create_discount(db, product_id, discount_data)


@router.get("/products/{product_id}/discounts", response_model=List[ProductDiscountResponse])
async def get_product_discounts(
    product_id: int,
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get all discounts for a product"""
    return ProductDiscountService.get_product_discounts(db, product_id, active_only=active_only)


@router.get("/discounts/{discount_id}", response_model=ProductDiscountResponse)
async def get_discount(
    discount_id: int,
    db: Session = Depends(get_db)
):
    """Get discount by ID"""
    discount = ProductDiscountService.get_discount(db, discount_id)
    if not discount:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discount not found"
        )
    return discount


@router.put("/discounts/{discount_id}", response_model=ProductDiscountResponse)
async def update_discount(
    discount_id: int,
    discount_data: ProductDiscountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update product discount (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update discounts"
        )
    
    discount = ProductDiscountService.update_discount(db, discount_id, discount_data)
    if not discount:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discount not found"
        )
    return discount


@router.delete("/discounts/{discount_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discount(
    discount_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete product discount (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete discounts"
        )
    
    if not ProductDiscountService.delete_discount(db, discount_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discount not found"
        )


@router.get("/products/{product_id}/price", response_model=dict)
async def calculate_product_price(
    product_id: int,
    quantity: int = Query(1, ge=1),
    amount: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_db)
):
    """Calculate discounted price for a product"""
    price_info = ProductDiscountService.calculate_discounted_price(
        db, product_id, quantity=quantity, amount=amount
    )
    
    if price_info["original_price"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return price_info