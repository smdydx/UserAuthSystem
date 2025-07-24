"""
Category service for business logic
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.category import Category, ProductTag
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    ProductTagCreate, ProductTagUpdate, ProductTagResponse
)


class CategoryService:
    """Category business logic service"""
    
    @staticmethod
    def create_category(db: Session, category_data: CategoryCreate) -> Category:
        """Create a new category"""
        # Check if slug already exists
        if db.query(Category).filter(Category.slug == category_data.slug).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this slug already exists"
            )
        
        # Validate parent category exists if specified
        if category_data.parent_id:
            parent = db.query(Category).filter(Category.id == category_data.parent_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found"
                )
        
        # Create category
        db_category = Category(**category_data.model_dump())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
    
    @staticmethod
    def get_category(db: Session, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        return db.query(Category).filter(Category.id == category_id).first()
    
    @staticmethod
    def get_category_by_slug(db: Session, slug: str) -> Optional[Category]:
        """Get category by slug"""
        return db.query(Category).filter(Category.slug == slug).first()
    
    @staticmethod
    def get_categories(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        parent_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[Category]:
        """Get categories with filters"""
        query = db.query(Category)
        
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        
        if is_active is not None:
            query = query.filter(Category.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_main_categories(db: Session, is_active: bool = True) -> List[Category]:
        """Get main categories (no parent)"""
        query = db.query(Category).filter(Category.parent_id.is_(None))
        if is_active:
            query = query.filter(Category.is_active == True)
        return query.all()
    
    @staticmethod
    def update_category(
        db: Session, 
        category_id: int, 
        category_data: CategoryUpdate
    ) -> Optional[Category]:
        """Update category"""
        db_category = db.query(Category).filter(Category.id == category_id).first()
        if not db_category:
            return None
        
        # Check slug uniqueness if being updated
        if category_data.slug and category_data.slug != db_category.slug:
            if db.query(Category).filter(
                and_(Category.slug == category_data.slug, Category.id != category_id)
            ).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category with this slug already exists"
                )
        
        # Update fields
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
        
        db.commit()
        db.refresh(db_category)
        return db_category
    
    @staticmethod
    def delete_category(db: Session, category_id: int) -> bool:
        """Delete category"""
        db_category = db.query(Category).filter(Category.id == category_id).first()
        if not db_category:
            return False
        
        # Check if category has subcategories
        subcategories = db.query(Category).filter(Category.parent_id == category_id).first()
        if subcategories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with subcategories"
            )
        
        # Check if category has products
        from app.models.product import Product
        products = db.query(Product).filter(Product.category_id == category_id).first()
        if products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with products"
            )
        
        db.delete(db_category)
        db.commit()
        return True


class ProductTagService:
    """Product tag business logic service"""
    
    @staticmethod
    def create_tag(db: Session, tag_data: ProductTagCreate) -> ProductTag:
        """Create a new product tag"""
        # Check if slug already exists
        if db.query(ProductTag).filter(ProductTag.slug == tag_data.slug).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this slug already exists"
            )
        
        # Check if name already exists
        if db.query(ProductTag).filter(ProductTag.name == tag_data.name).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this name already exists"
            )
        
        db_tag = ProductTag(**tag_data.model_dump())
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        return db_tag
    
    @staticmethod
    def get_tag(db: Session, tag_id: int) -> Optional[ProductTag]:
        """Get tag by ID"""
        return db.query(ProductTag).filter(ProductTag.id == tag_id).first()
    
    @staticmethod
    def get_tag_by_slug(db: Session, slug: str) -> Optional[ProductTag]:
        """Get tag by slug"""
        return db.query(ProductTag).filter(ProductTag.slug == slug).first()
    
    @staticmethod
    def get_tags(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[ProductTag]:
        """Get tags with optional search"""
        query = db.query(ProductTag)
        
        if search:
            query = query.filter(
                or_(
                    ProductTag.name.ilike(f"%{search}%"),
                    ProductTag.slug.ilike(f"%{search}%")
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_tag(
        db: Session, 
        tag_id: int, 
        tag_data: ProductTagUpdate
    ) -> Optional[ProductTag]:
        """Update tag"""
        db_tag = db.query(ProductTag).filter(ProductTag.id == tag_id).first()
        if not db_tag:
            return None
        
        # Check uniqueness
        if tag_data.slug and tag_data.slug != db_tag.slug:
            if db.query(ProductTag).filter(
                and_(ProductTag.slug == tag_data.slug, ProductTag.id != tag_id)
            ).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tag with this slug already exists"
                )
        
        if tag_data.name and tag_data.name != db_tag.name:
            if db.query(ProductTag).filter(
                and_(ProductTag.name == tag_data.name, ProductTag.id != tag_id)
            ).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tag with this name already exists"
                )
        
        # Update fields
        update_data = tag_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tag, field, value)
        
        db.commit()
        db.refresh(db_tag)
        return db_tag
    
    @staticmethod
    def delete_tag(db: Session, tag_id: int) -> bool:
        """Delete tag"""
        db_tag = db.query(ProductTag).filter(ProductTag.id == tag_id).first()
        if not db_tag:
            return False
        
        db.delete(db_tag)
        db.commit()
        return True