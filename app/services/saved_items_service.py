"""
Saved Items / Wishlist Service
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from fastapi import HTTPException, status

from app.models.cart import SavedItem
from app.models.product import Product, ProductVariant
from app.schemas.cart import SavedItemCreate, SavedItemUpdate


class SavedItemsService:
    """Saved items / wishlist management"""
    
    @staticmethod
    def save_item(
        db: Session,
        user_id: int,
        item_data: SavedItemCreate
    ) -> SavedItem:
        """Save item to user's list"""
        # Validate product exists
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Validate variant if specified
        if item_data.variant_id:
            variant = db.query(ProductVariant).filter(
                and_(
                    ProductVariant.id == item_data.variant_id,
                    ProductVariant.product_id == item_data.product_id
                )
            ).first()
            if not variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product variant not found"
                )
        
        # Check if item already saved
        existing_item = db.query(SavedItem).filter(
            and_(
                SavedItem.user_id == user_id,
                SavedItem.product_id == item_data.product_id,
                SavedItem.variant_id == item_data.variant_id,
                SavedItem.list_name == item_data.list_name
            )
        ).first()
        
        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item already saved to this list"
            )
        
        # Get current price for snapshot
        variant = None
        if item_data.variant_id:
            variant = db.query(ProductVariant).filter(ProductVariant.id == item_data.variant_id).first()
        
        saved_price = variant.price if variant and variant.price else product.price
        
        # Create saved item
        db_item = SavedItem(
            user_id=user_id,
            product_id=item_data.product_id,
            variant_id=item_data.variant_id,
            quantity=item_data.quantity,
            list_name=item_data.list_name,
            notes=item_data.notes,
            is_public=item_data.is_public,
            saved_price=saved_price
        )
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    
    @staticmethod
    def get_saved_items(
        db: Session,
        user_id: int,
        list_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[SavedItem]:
        """Get user's saved items"""
        query = db.query(SavedItem).filter(SavedItem.user_id == user_id).options(
            joinedload(SavedItem.product),
            joinedload(SavedItem.variant)
        )
        
        if list_name:
            query = query.filter(SavedItem.list_name == list_name)
        
        return query.order_by(desc(SavedItem.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_saved_item(
        db: Session,
        item_id: int,
        user_id: int
    ) -> Optional[SavedItem]:
        """Get specific saved item"""
        return db.query(SavedItem).filter(
            and_(SavedItem.id == item_id, SavedItem.user_id == user_id)
        ).first()
    
    @staticmethod
    def update_saved_item(
        db: Session,
        item_id: int,
        user_id: int,
        item_data: SavedItemUpdate
    ) -> Optional[SavedItem]:
        """Update saved item"""
        db_item = SavedItemsService.get_saved_item(db, item_id, user_id)
        if not db_item:
            return None
        
        # Update fields
        update_data = item_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        db.commit()
        db.refresh(db_item)
        return db_item
    
    @staticmethod
    def remove_saved_item(
        db: Session,
        item_id: int,
        user_id: int
    ) -> bool:
        """Remove item from saved list"""
        db_item = SavedItemsService.get_saved_item(db, item_id, user_id)
        if not db_item:
            return False
        
        db.delete(db_item)
        db.commit()
        return True
    
    @staticmethod
    def get_user_lists(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Get user's saved item lists with counts"""
        result = db.query(
            SavedItem.list_name,
            func.count(SavedItem.id).label('item_count')
        ).filter(SavedItem.user_id == user_id).group_by(SavedItem.list_name).all()
        
        return [
            {"list_name": row.list_name, "item_count": row.item_count}
            for row in result
        ]
    
    @staticmethod
    def move_to_cart(
        db: Session,
        item_id: int,
        user_id: int,
        cart_service
    ) -> bool:
        """Move saved item to cart"""
        saved_item = SavedItemsService.get_saved_item(db, item_id, user_id)
        if not saved_item:
            return False
        
        # Get or create user's cart
        cart = cart_service.get_or_create_cart(db, user_id=user_id)
        
        # Add to cart
        from app.schemas.cart import CartItemCreate
        cart_item_data = CartItemCreate(
            product_id=saved_item.product_id,
            variant_id=saved_item.variant_id,
            quantity=saved_item.quantity,
            notes=saved_item.notes
        )
        
        try:
            cart_service.add_item(db, cart.id, cart_item_data, user_id)
            # Remove from saved items
            SavedItemsService.remove_saved_item(db, item_id, user_id)
            return True
        except HTTPException:
            # Failed to add to cart (e.g., out of stock)
            return False