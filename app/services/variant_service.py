"""
Product variant service for business logic
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.product import ProductVariant, Product, VariantOption
from app.schemas.product import (
    ProductVariantCreate, ProductVariantUpdate, VariantOptionCreate
)


class ProductVariantService:
    """Product variant business logic service"""
    
    @staticmethod
    def create_variant(
        db: Session, 
        product_id: int, 
        variant_data: ProductVariantCreate
    ) -> ProductVariant:
        """Create a new product variant"""
        # Verify product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check if SKU already exists
        if db.query(ProductVariant).filter(ProductVariant.sku == variant_data.sku).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Variant with this SKU already exists"
            )
        
        # Create variant
        db_variant = ProductVariant(
            product_id=product_id,
            **variant_data.model_dump()
        )
        db.add(db_variant)
        db.commit()
        db.refresh(db_variant)
        return db_variant
    
    @staticmethod
    def get_variant(db: Session, variant_id: int) -> Optional[ProductVariant]:
        """Get variant by ID"""
        return db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    
    @staticmethod
    def get_product_variants(db: Session, product_id: int) -> List[ProductVariant]:
        """Get all variants for a product"""
        return db.query(ProductVariant).filter(
            ProductVariant.product_id == product_id
        ).all()
    
    @staticmethod
    def update_variant(
        db: Session, 
        variant_id: int, 
        variant_data: ProductVariantUpdate
    ) -> Optional[ProductVariant]:
        """Update product variant"""
        db_variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not db_variant:
            return None
        
        # Check SKU uniqueness if being updated
        if variant_data.sku and variant_data.sku != db_variant.sku:
            if db.query(ProductVariant).filter(
                and_(ProductVariant.sku == variant_data.sku, ProductVariant.id != variant_id)
            ).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Variant with this SKU already exists"
                )
        
        # Update fields
        update_data = variant_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_variant, field, value)
        
        db.commit()
        db.refresh(db_variant)
        return db_variant
    
    @staticmethod
    def delete_variant(db: Session, variant_id: int) -> bool:
        """Delete product variant"""
        db_variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not db_variant:
            return False
        
        db.delete(db_variant)
        db.commit()
        return True
    
    @staticmethod
    def update_variant_inventory(
        db: Session, 
        variant_id: int, 
        quantity: int
    ) -> Optional[ProductVariant]:
        """Update variant inventory quantity"""
        db_variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not db_variant:
            return None
        
        db_variant.inventory_quantity = quantity
        db.commit()
        db.refresh(db_variant)
        return db_variant


class VariantOptionService:
    """Variant option service"""
    
    @staticmethod
    def create_option(db: Session, option_data: VariantOptionCreate) -> VariantOption:
        """Create a new variant option"""
        db_option = VariantOption(**option_data.model_dump())
        db.add(db_option)
        db.commit()
        db.refresh(db_option)
        return db_option
    
    @staticmethod
    def get_options(
        db: Session, 
        option_name: Optional[str] = None
    ) -> List[VariantOption]:
        """Get variant options, optionally filtered by name"""
        query = db.query(VariantOption)
        if option_name:
            query = query.filter(VariantOption.name == option_name)
        return query.all()
    
    @staticmethod
    def get_option_names(db: Session) -> List[str]:
        """Get unique option names (e.g., Color, Size)"""
        return [row[0] for row in db.query(VariantOption.name).distinct().all()]
    
    @staticmethod
    def delete_option(db: Session, option_id: int) -> bool:
        """Delete variant option"""
        db_option = db.query(VariantOption).filter(VariantOption.id == option_id).first()
        if not db_option:
            return False
        
        db.delete(db_option)
        db.commit()
        return True