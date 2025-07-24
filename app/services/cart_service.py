"""
Cart Management Service
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import uuid
import json

from app.models.cart import Cart, CartItem, SavedItem, CartEvent, CartStatus
from app.models.product import Product, ProductVariant
from app.models.user import User
from app.schemas.cart import (
    CartCreate, CartUpdate, CartItemCreate, CartItemUpdate,
    CartSyncRequest, SavedItemCreate, SavedItemUpdate, BulkCartOperation
)
from app.services.discount_service import ProductDiscountService


class CartService:
    """Cart management business logic"""
    
    # Cart expiration time for anonymous users (30 days)
    ANONYMOUS_CART_EXPIRY = timedelta(days=30)
    
    @staticmethod
    def create_cart(
        db: Session, 
        cart_data: CartCreate, 
        user_id: Optional[int] = None
    ) -> Cart:
        """Create a new cart"""
        # Generate session token for anonymous carts
        session_token = cart_data.session_token
        if not session_token and not user_id:
            session_token = str(uuid.uuid4())
        
        # Set expiry for anonymous carts
        expires_at = None
        if not user_id:
            expires_at = datetime.utcnow() + CartService.ANONYMOUS_CART_EXPIRY
        
        db_cart = Cart(
            user_id=user_id,
            session_token=session_token,
            guest_email=cart_data.guest_email,
            currency=cart_data.currency,
            expires_at=expires_at,
            status=CartStatus.ACTIVE
        )
        
        db.add(db_cart)
        db.commit()
        db.refresh(db_cart)
        return db_cart
    
    @staticmethod
    def get_cart(
        db: Session, 
        cart_id: Optional[int] = None,
        user_id: Optional[int] = None,
        session_token: Optional[str] = None,
        include_items: bool = True
    ) -> Optional[Cart]:
        """Get cart by various identifiers"""
        query = db.query(Cart)
        
        if include_items:
            query = query.options(
                joinedload(Cart.items).joinedload(CartItem.product),
                joinedload(Cart.items).joinedload(CartItem.variant)
            )
        
        if cart_id:
            return query.filter(Cart.id == cart_id).first()
        elif user_id:
            return query.filter(
                and_(Cart.user_id == user_id, Cart.status == CartStatus.ACTIVE)
            ).first()
        elif session_token:
            return query.filter(
                and_(
                    Cart.session_token == session_token, 
                    Cart.status == CartStatus.ACTIVE,
                    or_(Cart.expires_at.is_(None), Cart.expires_at > datetime.utcnow())
                )
            ).first()
        
        return None
    
    @staticmethod
    def get_or_create_cart(
        db: Session,
        user_id: Optional[int] = None,
        session_token: Optional[str] = None,
        cart_data: Optional[CartCreate] = None
    ) -> Cart:
        """Get existing cart or create new one"""
        # Try to get existing cart
        cart = CartService.get_cart(
            db, user_id=user_id, session_token=session_token
        )
        
        if cart:
            # Update last activity
            cart.last_activity = datetime.utcnow()
            db.commit()
            return cart
        
        # Create new cart
        if not cart_data:
            cart_data = CartCreate(session_token=session_token)
        
        return CartService.create_cart(db, cart_data, user_id)
    
    @staticmethod
    def add_item(
        db: Session, 
        cart_id: int, 
        item_data: CartItemCreate,
        user_id: Optional[int] = None
    ) -> CartItem:
        """Add item to cart with validation"""
        # Get cart
        cart = CartService.get_cart(db, cart_id=cart_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )
        
        # Validate product exists and is available
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if product.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product is not available"
            )
        
        # Validate variant if specified
        variant = None
        if item_data.variant_id:
            variant = db.query(ProductVariant).filter(
                and_(
                    ProductVariant.id == item_data.variant_id,
                    ProductVariant.product_id == item_data.product_id,
                    ProductVariant.is_active == True
                )
            ).first()
            if not variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product variant not found"
                )
        
        # Check inventory
        available_quantity = variant.inventory_quantity if variant else product.inventory_quantity
        if available_quantity < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {available_quantity} items available in stock"
            )
        
        # Check if item already exists in cart
        existing_item = db.query(CartItem).filter(
            and_(
                CartItem.cart_id == cart_id,
                CartItem.product_id == item_data.product_id,
                CartItem.variant_id == item_data.variant_id
            )
        ).first()
        
        if existing_item:
            # Update quantity
            new_quantity = existing_item.quantity + item_data.quantity
            if available_quantity < new_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Total quantity ({new_quantity}) exceeds available stock ({available_quantity})"
                )
            
            existing_item.quantity = new_quantity
            existing_item.updated_at = datetime.utcnow()
            
            # Recalculate pricing
            CartService._update_item_pricing(db, existing_item)
            
            # Log event
            CartService._log_cart_event(
                db, cart_id, "update_quantity", user_id, 
                item_data.product_id, item_data.variant_id,
                quantity_change=item_data.quantity
            )
            
            db.commit()
            db.refresh(existing_item)
            
            # Update cart totals
            CartService._update_cart_totals(db, cart_id)
            
            return existing_item
        
        # Calculate pricing
        base_price = variant.price if variant and variant.price else product.price
        
        # Get best discount
        pricing_info = ProductDiscountService.calculate_discounted_price(
            db, item_data.product_id, quantity=item_data.quantity
        )
        
        unit_price = pricing_info["discounted_price"]
        original_price = pricing_info["original_price"]
        discount_amount = pricing_info["discount_amount"]
        total_price = unit_price * item_data.quantity
        
        # Create product snapshot
        product_snapshot = {
            "name": product.name,
            "sku": product.sku,
            "slug": product.slug,
            "image_url": product.images[0].url if product.images else None,
            "variant_title": variant.title if variant else None,
            "variant_options": variant.options if variant else None
        }
        
        # Create cart item
        db_item = CartItem(
            cart_id=cart_id,
            product_id=item_data.product_id,
            variant_id=item_data.variant_id,
            quantity=item_data.quantity,
            unit_price=unit_price,
            original_price=original_price,
            discount_amount=discount_amount,
            total_price=total_price,
            product_snapshot=product_snapshot,
            custom_options=item_data.custom_options,
            notes=item_data.notes
        )
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        # Log event
        CartService._log_cart_event(
            db, cart_id, "add_item", user_id,
            item_data.product_id, item_data.variant_id,
            quantity_change=item_data.quantity,
            price_at_event=unit_price
        )
        
        # Update cart totals
        CartService._update_cart_totals(db, cart_id)
        
        return db_item
    
    @staticmethod
    def update_item(
        db: Session,
        item_id: int,
        item_data: CartItemUpdate,
        user_id: Optional[int] = None
    ) -> Optional[CartItem]:
        """Update cart item"""
        db_item = db.query(CartItem).filter(CartItem.id == item_id).first()
        if not db_item:
            return None
        
        # Validate quantity if being updated
        if item_data.quantity is not None:
            # Check inventory
            product = db_item.product
            variant = db_item.variant
            available_quantity = variant.inventory_quantity if variant else product.inventory_quantity
            
            if available_quantity < item_data.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {available_quantity} items available in stock"
                )
            
            old_quantity = db_item.quantity
            db_item.quantity = item_data.quantity
            
            # Log quantity change
            CartService._log_cart_event(
                db, db_item.cart_id, "update_quantity", user_id,
                db_item.product_id, db_item.variant_id,
                quantity_change=item_data.quantity - old_quantity
            )
        
        # Update other fields
        if item_data.custom_options is not None:
            db_item.custom_options = item_data.custom_options
        
        if item_data.notes is not None:
            db_item.notes = item_data.notes
        
        db_item.updated_at = datetime.utcnow()
        
        # Recalculate pricing
        CartService._update_item_pricing(db, db_item)
        
        db.commit()
        db.refresh(db_item)
        
        # Update cart totals
        CartService._update_cart_totals(db, db_item.cart_id)
        
        return db_item
    
    @staticmethod
    def remove_item(
        db: Session,
        item_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """Remove item from cart"""
        db_item = db.query(CartItem).filter(CartItem.id == item_id).first()
        if not db_item:
            return False
        
        cart_id = db_item.cart_id
        
        # Log event
        CartService._log_cart_event(
            db, cart_id, "remove_item", user_id,
            db_item.product_id, db_item.variant_id,
            quantity_change=-db_item.quantity
        )
        
        db.delete(db_item)
        db.commit()
        
        # Update cart totals
        CartService._update_cart_totals(db, cart_id)
        
        return True
    
    @staticmethod
    def clear_cart(
        db: Session,
        cart_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """Clear all items from cart"""
        cart = CartService.get_cart(db, cart_id=cart_id)
        if not cart:
            return False
        
        # Remove all items
        db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
        
        # Reset cart totals
        cart.items_count = 0
        cart.subtotal = 0.00
        cart.discount_total = 0.00
        cart.tax_total = 0.00
        cart.total = 0.00
        cart.updated_at = datetime.utcnow()
        
        # Log event
        CartService._log_cart_event(
            db, cart_id, "clear_cart", user_id
        )
        
        db.commit()
        return True
    
    @staticmethod
    def sync_cart_on_login(
        db: Session,
        user_id: int,
        sync_request: CartSyncRequest
    ) -> Cart:
        """Sync anonymous cart with user account on login"""
        # Get user's existing cart
        user_cart = CartService.get_cart(db, user_id=user_id)
        
        # Get anonymous cart
        anon_cart = CartService.get_cart(db, session_token=sync_request.session_token)
        
        if not anon_cart:
            # No anonymous cart to sync
            if user_cart:
                return user_cart
            else:
                # Create new cart for user
                return CartService.create_cart(db, CartCreate(), user_id)
        
        if not user_cart:
            # No existing user cart, just assign anonymous cart to user
            anon_cart.user_id = user_id
            anon_cart.session_token = None
            anon_cart.expires_at = None
            anon_cart.updated_at = datetime.utcnow()
            db.commit()
            return anon_cart
        
        # Both carts exist - merge based on strategy
        if sync_request.merge_strategy == "replace":
            # Replace user cart with anonymous cart
            CartService.clear_cart(db, user_cart.id, user_id)
            
            # Move items from anonymous cart to user cart
            for item in anon_cart.items:
                item.cart_id = user_cart.id
            
            db.commit()
            
            # Delete anonymous cart
            db.delete(anon_cart)
            db.commit()
            
            # Update totals
            CartService._update_cart_totals(db, user_cart.id)
            
            return user_cart
        
        else:  # merge strategy
            # Merge anonymous cart items into user cart
            for anon_item in anon_cart.items:
                # Check if item already exists in user cart
                existing_item = db.query(CartItem).filter(
                    and_(
                        CartItem.cart_id == user_cart.id,
                        CartItem.product_id == anon_item.product_id,
                        CartItem.variant_id == anon_item.variant_id
                    )
                ).first()
                
                if existing_item:
                    # Update quantity (with stock validation)
                    try:
                        CartService.update_item(
                            db, existing_item.id,
                            CartItemUpdate(quantity=existing_item.quantity + anon_item.quantity),
                            user_id
                        )
                    except HTTPException:
                        # Stock limit reached, skip this item
                        continue
                else:
                    # Move item to user cart
                    anon_item.cart_id = user_cart.id
            
            db.commit()
            
            # Delete anonymous cart
            db.delete(anon_cart)
            db.commit()
            
            # Update totals
            CartService._update_cart_totals(db, user_cart.id)
            
            return user_cart
    
    @staticmethod
    def validate_cart(db: Session, cart_id: int) -> Dict[str, Any]:
        """Validate cart items against current product data"""
        cart = CartService.get_cart(db, cart_id=cart_id, include_items=True)
        if not cart:
            return {"is_valid": False, "errors": [{"type": "cart_not_found"}]}
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "updated_items": []
        }
        
        for item in cart.items:
            # Check product availability
            product = item.product
            if not product or product.status != "active":
                validation_result["errors"].append({
                    "type": "product_unavailable",
                    "item_id": item.id,
                    "product_id": item.product_id,
                    "message": "Product is no longer available"
                })
                validation_result["is_valid"] = False
                continue
            
            # Check variant availability
            if item.variant_id:
                variant = item.variant
                if not variant or not variant.is_active:
                    validation_result["errors"].append({
                        "type": "variant_unavailable",
                        "item_id": item.id,
                        "variant_id": item.variant_id,
                        "message": "Product variant is no longer available"
                    })
                    validation_result["is_valid"] = False
                    continue
            
            # Check stock availability
            available_stock = item.variant.inventory_quantity if item.variant else product.inventory_quantity
            if available_stock < item.quantity:
                if available_stock == 0:
                    validation_result["errors"].append({
                        "type": "out_of_stock",
                        "item_id": item.id,
                        "message": "Item is out of stock"
                    })
                    validation_result["is_valid"] = False
                else:
                    validation_result["warnings"].append({
                        "type": "limited_stock",
                        "item_id": item.id,
                        "available_quantity": available_stock,
                        "requested_quantity": item.quantity,
                        "message": f"Only {available_stock} items available"
                    })
            
            # Check price changes
            current_pricing = ProductDiscountService.calculate_discounted_price(
                db, item.product_id, quantity=item.quantity
            )
            
            if abs(float(current_pricing["discounted_price"]) - float(item.unit_price)) > 0.01:
                validation_result["warnings"].append({
                    "type": "price_change",
                    "item_id": item.id,
                    "old_price": float(item.unit_price),
                    "new_price": current_pricing["discounted_price"],
                    "message": "Price has changed since adding to cart"
                })
                
                # Update item pricing
                CartService._update_item_pricing(db, item, current_pricing)
                validation_result["updated_items"].append(item)
        
        if validation_result["updated_items"]:
            db.commit()
            CartService._update_cart_totals(db, cart_id)
        
        return validation_result
    
    @staticmethod
    def _update_item_pricing(
        db: Session, 
        item: CartItem, 
        pricing_info: Optional[Dict] = None
    ):
        """Update cart item pricing"""
        if not pricing_info:
            pricing_info = ProductDiscountService.calculate_discounted_price(
                db, item.product_id, quantity=item.quantity
            )
        
        item.unit_price = pricing_info["discounted_price"]
        item.original_price = pricing_info["original_price"]
        item.discount_amount = pricing_info["discount_amount"]
        item.total_price = float(item.unit_price) * item.quantity
        item.updated_at = datetime.utcnow()
    
    @staticmethod
    def _update_cart_totals(db: Session, cart_id: int):
        """Update cart total calculations"""
        cart = db.query(Cart).filter(Cart.id == cart_id).first()
        if not cart:
            return
        
        # Calculate totals from items
        items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
        
        items_count = sum(item.quantity for item in items)
        subtotal = sum(float(item.total_price) for item in items)
        discount_total = sum(float(item.discount_amount) * item.quantity for item in items)
        
        # Tax calculation (placeholder - implement based on business rules)
        tax_total = 0.00  # Can be calculated based on location, product type, etc.
        
        total = subtotal + tax_total
        
        # Update cart
        cart.items_count = items_count
        cart.subtotal = subtotal
        cart.discount_total = discount_total
        cart.tax_total = tax_total
        cart.total = total
        cart.updated_at = datetime.utcnow()
        
        db.commit()
    
    @staticmethod
    def _log_cart_event(
        db: Session,
        cart_id: int,
        event_type: str,
        user_id: Optional[int] = None,
        product_id: Optional[int] = None,
        variant_id: Optional[int] = None,
        quantity_change: Optional[int] = None,
        price_at_event: Optional[float] = None,
        event_data: Optional[Dict] = None
    ):
        """Log cart event for analytics"""
        event = CartEvent(
            cart_id=cart_id,
            user_id=user_id,
            event_type=event_type,
            product_id=product_id,
            variant_id=variant_id,
            quantity_change=quantity_change,
            price_at_event=price_at_event,
            event_data=event_data
        )
        
        db.add(event)
        # Note: Not committing here as it's usually called within another transaction