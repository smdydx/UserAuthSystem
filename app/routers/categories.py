"""
Category API routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.services.category_service import CategoryService, ProductTagService
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    ProductTagCreate, ProductTagUpdate, ProductTagResponse
)

router = APIRouter()

# ===============================
# CATEGORY ENDPOINTS
# ===============================

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new category (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create categories"
        )
    
    return CategoryService.create_category(db, category_data)


@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    parent_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get categories with optional filters"""
    return CategoryService.get_categories(
        db, skip=skip, limit=limit, parent_id=parent_id, is_active=is_active
    )


@router.get("/categories/main", response_model=List[CategoryResponse])
async def get_main_categories(
    is_active: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get main categories (no parent)"""
    return CategoryService.get_main_categories(db, is_active=is_active)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """Get category by ID"""
    category = CategoryService.get_category(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.get("/categories/slug/{slug}", response_model=CategoryResponse)
async def get_category_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get category by slug"""
    category = CategoryService.get_category_by_slug(db, slug)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update category (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update categories"
        )
    
    category = CategoryService.update_category(db, category_id, category_data)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete category (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete categories"
        )
    
    if not CategoryService.delete_category(db, category_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )


# ===============================
# PRODUCT TAG ENDPOINTS
# ===============================

@router.post("/tags", response_model=ProductTagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: ProductTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new product tag (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create tags"
        )
    
    return ProductTagService.create_tag(db, tag_data)


@router.get("/tags", response_model=List[ProductTagResponse])
async def get_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get product tags with optional search"""
    return ProductTagService.get_tags(db, skip=skip, limit=limit, search=search)


@router.get("/tags/{tag_id}", response_model=ProductTagResponse)
async def get_tag(
    tag_id: int,
    db: Session = Depends(get_db)
):
    """Get tag by ID"""
    tag = ProductTagService.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag


@router.get("/tags/slug/{slug}", response_model=ProductTagResponse)
async def get_tag_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get tag by slug"""
    tag = ProductTagService.get_tag_by_slug(db, slug)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag


@router.put("/tags/{tag_id}", response_model=ProductTagResponse)
async def update_tag(
    tag_id: int,
    tag_data: ProductTagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update tag (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update tags"
        )
    
    tag = ProductTagService.update_tag(db, tag_id, tag_data)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete tag (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete tags"
        )
    
    if not ProductTagService.delete_tag(db, tag_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )