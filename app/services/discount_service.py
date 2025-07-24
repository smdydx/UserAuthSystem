"""
Product discount service for pricing rules
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from datetime import datetime

from app.models.product import ProductDiscount, Product
from app.schemas.product import ProductDiscountCreate, ProductDiscountUpdate


class ProductDiscountService:
    """Product discount business logic service"""
    
    @staticmethod
    def create_discount(
        db: Session, 
        product_id: int, 
        discount_data: ProductDiscountCreate
    ) -> ProductDiscount:
        """Create a new product discount"""
        # Verify product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Create discount
        db_discount = ProductDiscount(
            product_id=product_id,
            **discount_data.model_dump()
        )
        db.add(db_discount)
        db.commit()
        db.refresh(db_discount)
        return db_discount
    
    @staticmethod
    def get_discount(db: Session, discount_id: int) -> Optional[ProductDiscount]:
        """Get discount by ID"""
        return db.query(ProductDiscount).filter(ProductDiscount.id == discount_id).first()
    
    @staticmethod
    def get_product_discounts(
        db: Session, 
        product_id: int,
        active_only: bool = False
    ) -> List[ProductDiscount]:
        """Get all discounts for a product"""
        query = db.query(ProductDiscount).filter(ProductDiscount.product_id == product_id)
        
        if active_only:
            now = datetime.utcnow()
            query = query.filter(
                and_(
                    ProductDiscount.is_active == True,
                    or_(
                        ProductDiscount.starts_at.is_(None),
                        ProductDiscount.starts_at <= now
                    ),
                    or_(
                        ProductDiscount.ends_at.is_(None),
                        ProductDiscount.ends_at > now
                    )
                )
            )
        
        return query.all()
    
    @staticmethod
    def get_active_discounts(db: Session, product_id: int) -> List[ProductDiscount]:
        """Get currently active discounts for a product"""
        return ProductDiscountService.get_product_discounts(
            db, product_id, active_only=True
        )
    
    @staticmethod
    def update_discount(
        db: Session, 
        discount_id: int, 
        discount_data: ProductDiscountUpdate
    ) -> Optional[ProductDiscount]:
        """Update product discount"""
        db_discount = db.query(ProductDiscount).filter(ProductDiscount.id == discount_id).first()
        if not db_discount:
            return None
        
        # Update fields
        update_data = discount_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_discount, field, value)
        
        db.commit()
        db.refresh(db_discount)
        return db_discount
    
    @staticmethod
    def delete_discount(db: Session, discount_id: int) -> bool:
        """Delete product discount"""
        db_discount = db.query(ProductDiscount).filter(ProductDiscount.id == discount_id).first()
        if not db_discount:
            return False
        
        db.delete(db_discount)
        db.commit()
        return True
    
    @staticmethod
    def calculate_discounted_price(
        db: Session, 
        product_id: int, 
        quantity: int = 1,
        amount: Optional[float] = None
    ) -> dict:
        """
        Calculate the best discount for a product based on quantity and amount
        Returns the discounted price and discount details
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"original_price": 0, "discounted_price": 0, "discount": None}
        
        original_price = float(product.price)
        total_amount = amount or (original_price * quantity)
        
        # Get active discounts
        active_discounts = ProductDiscountService.get_active_discounts(db, product_id)
        
        best_discount = None
        best_discounted_price = original_price
        
        for discount in active_discounts:
            # Check if discount conditions are met
            if quantity < discount.min_quantity:
                continue
            
            if discount.min_amount and total_amount < float(discount.min_amount):
                continue
            
            # Check usage limit
            if discount.usage_limit and discount.usage_count >= discount.usage_limit:
                continue
            
            # Calculate discounted price
            if discount.discount_type == "percentage":
                discount_amount = original_price * (float(discount.value) / 100)
            else:  # fixed_amount
                discount_amount = float(discount.value)
            
            discounted_price = max(0, original_price - discount_amount)
            
            # Check if this is the best discount
            if discounted_price < best_discounted_price:
                best_discounted_price = discounted_price
                best_discount = discount
        
        discount_percentage = None
        if best_discount and original_price > 0:
            discount_percentage = ((original_price - best_discounted_price) / original_price) * 100
        
        return {
            "original_price": original_price,
            "discounted_price": best_discounted_price,
            "discount_amount": original_price - best_discounted_price,
            "discount_percentage": discount_percentage,
            "discount": {
                "id": best_discount.id,
                "name": best_discount.name,
                "type": best_discount.discount_type,
                "value": float(best_discount.value)
            } if best_discount else None
        }
    
    @staticmethod
    def apply_discount_usage(db: Session, discount_id: int) -> bool:
        """Increment usage count for a discount"""
        discount = db.query(ProductDiscount).filter(ProductDiscount.id == discount_id).first()
        if not discount:
            return False
        
        discount.usage_count += 1
        db.commit()
        return True