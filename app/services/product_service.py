"""
Product service for business logic
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from fastapi import HTTPException, status
from datetime import datetime

from app.models.product import (
    Product, ProductImage, ProductVariant, ProductDiscount, 
    ProductStatus, product_tag_associations
)
from app.models.category import Category, ProductTag
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductSummary, ProductResponse,
    ProductSearchFilters, ProductImageCreate, ProductVariantCreate,
    ProductDiscountCreate
)


class ProductService:
    """Product business logic service"""
    
    @staticmethod
    def create_product(db: Session, product_data: ProductCreate) -> Product:
        """Create a new product"""
        # Check if SKU already exists
        if db.query(Product).filter(Product.sku == product_data.sku).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product with this SKU already exists"
            )
        
        # Check if slug already exists
        if db.query(Product).filter(Product.slug == product_data.slug).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product with this slug already exists"
            )
        
        # Validate category exists if specified
        if product_data.category_id:
            category = db.query(Category).filter(Category.id == product_data.category_id).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
        
        # Create main product (excluding related data)
        product_dict = product_data.model_dump(exclude={'tag_ids', 'images', 'variants', 'discounts'})
        db_product = Product(**product_dict)
        
        # Set published_at if status is active
        if product_data.status == ProductStatus.ACTIVE:
            db_product.published_at = datetime.utcnow()
        
        db.add(db_product)
        db.flush()  # Get the ID
        
        # Add tags
        if product_data.tag_ids:
            tags = db.query(ProductTag).filter(ProductTag.id.in_(product_data.tag_ids)).all()
            db_product.tags = tags
        
        # Add images
        if product_data.images:
            for i, image_data in enumerate(product_data.images):
                db_image = ProductImage(
                    product_id=db_product.id,
                    **image_data.model_dump()
                )
                # Set first image as primary if none specified
                if i == 0 and not any(img.is_primary for img in product_data.images):
                    db_image.is_primary = True
                db.add(db_image)
        
        # Add variants
        if product_data.variants:
            for variant_data in product_data.variants:
                # Check variant SKU uniqueness
                if db.query(ProductVariant).filter(ProductVariant.sku == variant_data.sku).first():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Variant SKU '{variant_data.sku}' already exists"
                    )
                db_variant = ProductVariant(
                    product_id=db_product.id,
                    **variant_data.model_dump()
                )
                db.add(db_variant)
        
        # Add discounts
        if product_data.discounts:
            for discount_data in product_data.discounts:
                db_discount = ProductDiscount(
                    product_id=db_product.id,
                    **discount_data.model_dump()
                )
                db.add(db_discount)
        
        db.commit()
        db.refresh(db_product)
        return db_product
    
    @staticmethod
    def get_product(
        db: Session, 
        product_id: Optional[int] = None, 
        slug: Optional[str] = None
    ) -> Optional[Product]:
        """Get product by ID or slug with all relationships"""
        query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.images),
            joinedload(Product.variants),
            joinedload(Product.tags),
            joinedload(Product.discounts)
        )
        
        if product_id:
            return query.filter(Product.id == product_id).first()
        elif slug:
            return query.filter(Product.slug == slug).first()
        return None
    
    @staticmethod
    def get_products(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[ProductSearchFilters] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Product], int]:
        """Get products with filters and pagination"""
        query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.images)
        )
        
        # Apply filters
        if filters:
            if filters.category_id:
                query = query.filter(Product.category_id == filters.category_id)
            
            if filters.tag_ids:
                query = query.join(product_tag_associations).filter(
                    product_tag_associations.c.tag_id.in_(filters.tag_ids)
                )
            
            if filters.status:
                query = query.filter(Product.status == filters.status)
            
            if filters.is_featured is not None:
                query = query.filter(Product.is_featured == filters.is_featured)
            
            if filters.min_price:
                query = query.filter(Product.price >= filters.min_price)
            
            if filters.max_price:
                query = query.filter(Product.price <= filters.max_price)
            
            if filters.in_stock is not None:
                if filters.in_stock:
                    query = query.filter(Product.inventory_quantity > 0)
                else:
                    query = query.filter(Product.inventory_quantity <= 0)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Product.name.ilike(search_term),
                        Product.description.ilike(search_term),
                        Product.sku.ilike(search_term)
                    )
                )
        
        # Apply sorting
        sort_column = getattr(Product, sort_by, Product.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Get total count before applying pagination
        total = query.count()
        
        # Apply pagination
        products = query.offset(skip).limit(limit).all()
        
        return products, total
    
    @staticmethod
    def update_product(
        db: Session, 
        product_id: int, 
        product_data: ProductUpdate
    ) -> Optional[Product]:
        """Update product"""
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if not db_product:
            return None
        
        # Check SKU uniqueness if being updated
        if product_data.sku and product_data.sku != db_product.sku:
            if db.query(Product).filter(
                and_(Product.sku == product_data.sku, Product.id != product_id)
            ).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product with this SKU already exists"
                )
        
        # Check slug uniqueness if being updated
        if product_data.slug and product_data.slug != db_product.slug:
            if db.query(Product).filter(
                and_(Product.slug == product_data.slug, Product.id != product_id)
            ).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product with this slug already exists"
                )
        
        # Update fields
        update_data = product_data.model_dump(exclude_unset=True, exclude={'tag_ids'})
        for field, value in update_data.items():
            setattr(db_product, field, value)
        
        # Update published_at if status changed to active
        if product_data.status == ProductStatus.ACTIVE and db_product.published_at is None:
            db_product.published_at = datetime.utcnow()
        
        # Update tags if provided
        if product_data.tag_ids is not None:
            tags = db.query(ProductTag).filter(ProductTag.id.in_(product_data.tag_ids)).all()
            db_product.tags = tags
        
        db.commit()
        db.refresh(db_product)
        return db_product
    
    @staticmethod
    def delete_product(db: Session, product_id: int) -> bool:
        """Delete product"""
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if not db_product:
            return False
        
        db.delete(db_product)
        db.commit()
        return True
    
    @staticmethod
    def get_featured_products(db: Session, limit: int = 10) -> List[Product]:
        """Get featured products"""
        return db.query(Product).filter(
            and_(Product.is_featured == True, Product.status == ProductStatus.ACTIVE)
        ).options(
            joinedload(Product.images)
        ).limit(limit).all()
    
    @staticmethod
    def get_products_by_category(
        db: Session, 
        category_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Product]:
        """Get products by category"""
        return db.query(Product).filter(
            and_(Product.category_id == category_id, Product.status == ProductStatus.ACTIVE)
        ).options(
            joinedload(Product.images)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def search_products(
        db: Session, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Product]:
        """Search products by name, description, or SKU"""
        search_pattern = f"%{search_term}%"
        return db.query(Product).filter(
            and_(
                Product.status == ProductStatus.ACTIVE,
                or_(
                    Product.name.ilike(search_pattern),
                    Product.description.ilike(search_pattern),
                    Product.sku.ilike(search_pattern)
                )
            )
        ).options(
            joinedload(Product.images)
        ).offset(skip).limit(limit).all()


class ProductImageService:
    """Product image service"""
    
    @staticmethod
    def add_product_image(
        db: Session, 
        product_id: int, 
        image_data: ProductImageCreate
    ) -> ProductImage:
        """Add image to product"""
        # Verify product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # If this is set as primary, unset other primary images
        if image_data.is_primary:
            db.query(ProductImage).filter(
                and_(ProductImage.product_id == product_id, ProductImage.is_primary == True)
            ).update({"is_primary": False})
        
        db_image = ProductImage(product_id=product_id, **image_data.model_dump())
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return db_image
    
    @staticmethod
    def delete_product_image(db: Session, image_id: int) -> bool:
        """Delete product image"""
        db_image = db.query(ProductImage).filter(ProductImage.id == image_id).first()
        if not db_image:
            return False
        
        db.delete(db_image)
        db.commit()
        return True
    
    @staticmethod
    def set_primary_image(db: Session, product_id: int, image_id: int) -> bool:
        """Set image as primary for product"""
        # Unset all primary images for the product
        db.query(ProductImage).filter(
            and_(ProductImage.product_id == product_id, ProductImage.is_primary == True)
        ).update({"is_primary": False})
        
        # Set the specified image as primary
        result = db.query(ProductImage).filter(
            and_(ProductImage.id == image_id, ProductImage.product_id == product_id)
        ).update({"is_primary": True})
        
        if result:
            db.commit()
            return True
        return False