"""
Cart Management API Routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user, get_current_active_user
from app.models.user import User
from app.services.cart_service import CartService
from app.services.saved_items_service import SavedItemsService
from app.schemas.cart import (
    CartCreate, CartUpdate, CartResponse, CartSummary,
    CartItemCreate, CartItemUpdate, CartItemResponse,
    CartSyncRequest, BulkCartOperation, CartValidationResponse,
    SavedItemCreate, SavedItemUpdate, SavedItemResponse
)

router = APIRouter()

# ===============================
# CART MANAGEMENT ENDPOINTS
# ===============================

@router.post("/cart", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def create_cart(
    cart_data: CartCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Create a new cart (for logged-in or anonymous users)"""
    user_id = current_user.id if current_user else None
    return CartService.create_cart(db, cart_data, user_id)


@router.get("/cart", response_model=CartResponse)
async def get_cart(
    session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get current user's cart or anonymous cart by session token"""
    if current_user:
        cart = CartService.get_cart(db, user_id=current_user.id)
    elif session_token:
        cart = CartService.get_cart(db, session_token=session_token)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either login or provide session token in X-Session-Token header"
        )
    
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    return cart


@router.get("/cart/summary", response_model=CartSummary)
async def get_cart_summary(
    session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get cart summary for quick display (items count, total, etc.)"""
    if current_user:
        cart = CartService.get_cart(db, user_id=current_user.id, include_items=False)
    elif session_token:
        cart = CartService.get_cart(db, session_token=session_token, include_items=False)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either login or provide session token"
        )
    
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    return cart


@router.put("/cart/{cart_id}", response_model=CartResponse)
async def update_cart(
    cart_id: int,
    cart_data: CartUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Update cart metadata (shipping address, billing address, etc.)"""
    cart = CartService.get_cart(db, cart_id=cart_id)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    # Update fields
    update_data = cart_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cart, field, value)
    
    db.commit()
    db.refresh(cart)
    return cart


@router.post("/cart/sync", response_model=CartResponse)
async def sync_cart_on_login(
    sync_request: CartSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync anonymous cart with user account on login"""
    return CartService.sync_cart_on_login(db, current_user.id, sync_request)


@router.get("/cart/{cart_id}/validate", response_model=CartValidationResponse)
async def validate_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Validate cart items against current product data and pricing"""
    return CartService.validate_cart(db, cart_id)


@router.delete("/cart/{cart_id}/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Clear all items from cart"""
    user_id = current_user.id if current_user else None
    
    if not CartService.clear_cart(db, cart_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )


# ===============================
# CART ITEMS ENDPOINTS
# ===============================

@router.post("/cart/{cart_id}/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
    cart_id: int,
    item_data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Add item to cart with stock and pricing validation"""
    user_id = current_user.id if current_user else None
    return CartService.add_item(db, cart_id, item_data, user_id)


@router.post("/cart/{cart_id}/items/bulk", response_model=List[CartItemResponse])
async def add_bulk_items_to_cart(
    cart_id: int,
    bulk_data: BulkCartOperation,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Add multiple items to cart at once"""
    user_id = current_user.id if current_user else None
    added_items = []
    
    for item_data in bulk_data.items:
        try:
            item = CartService.add_item(db, cart_id, item_data, user_id)
            added_items.append(item)
        except HTTPException as e:
            # Log error but continue with other items
            continue
    
    return added_items


@router.put("/cart/items/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Update cart item (quantity, notes, custom options)"""
    user_id = current_user.id if current_user else None
    
    item = CartService.update_item(db, item_id, item_data, user_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    return item


@router.delete("/cart/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Remove item from cart"""
    user_id = current_user.id if current_user else None
    
    if not CartService.remove_item(db, item_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )


# ===============================
# GUEST CART UTILITIES
# ===============================

@router.get("/cart/guest/create", response_model=dict)
async def create_guest_session():
    """Create a session token for anonymous cart management"""
    import uuid
    session_token = str(uuid.uuid4())
    return {
        "session_token": session_token,
        "expires_in": 30 * 24 * 60 * 60,  # 30 days in seconds
        "instructions": "Store this token in localStorage and send in X-Session-Token header"
    }


@router.get("/cart/guest/{session_token}", response_model=CartResponse)
async def get_guest_cart(
    session_token: str,
    db: Session = Depends(get_db)
):
    """Get guest cart by session token"""
    cart = CartService.get_cart(db, session_token=session_token)
    if not cart:
        # Create new guest cart
        cart_data = CartCreate(session_token=session_token)
        cart = CartService.create_cart(db, cart_data)
    
    return cart


# ===============================
# SAVED ITEMS / WISHLIST ENDPOINTS
# ===============================

@router.post("/saved-items", response_model=SavedItemResponse, status_code=status.HTTP_201_CREATED)
async def save_item(
    item_data: SavedItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Save item to user's wishlist or custom list"""
    return SavedItemsService.save_item(db, current_user.id, item_data)


@router.get("/saved-items", response_model=List[SavedItemResponse])
async def get_saved_items(
    list_name: Optional[str] = Query("wishlist"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's saved items from specific list"""
    return SavedItemsService.get_saved_items(
        db, current_user.id, list_name=list_name, skip=skip, limit=limit
    )


@router.get("/saved-items/lists", response_model=List[dict])
async def get_saved_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's saved item lists with counts"""
    return SavedItemsService.get_user_lists(db, current_user.id)


@router.put("/saved-items/{item_id}", response_model=SavedItemResponse)
async def update_saved_item(
    item_id: int,
    item_data: SavedItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update saved item"""
    item = SavedItemsService.update_saved_item(db, item_id, current_user.id, item_data)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved item not found"
        )
    return item


@router.delete("/saved-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_saved_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove item from saved list"""
    if not SavedItemsService.remove_saved_item(db, item_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved item not found"
        )


@router.post("/saved-items/{item_id}/move-to-cart", status_code=status.HTTP_200_OK)
async def move_saved_item_to_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Move saved item to cart"""
    success = SavedItemsService.move_to_cart(db, item_id, current_user.id, CartService)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to move item to cart (may be out of stock)"
        )
    
    return {"message": "Item moved to cart successfully"}


# ===============================
# CART ANALYTICS ENDPOINTS (ADMIN)
# ===============================

@router.get("/cart/analytics/abandoned", response_model=List[dict])
async def get_abandoned_carts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get abandoned carts for analytics (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access cart analytics"
        )
    
    from datetime import datetime, timedelta
    from app.models.cart import Cart, CartStatus
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    abandoned_carts = db.query(Cart).filter(
        and_(
            Cart.status == CartStatus.ACTIVE,
            Cart.items_count > 0,
            Cart.last_activity < cutoff_date
        )
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "cart_id": cart.id,
            "user_id": cart.user_id,
            "items_count": cart.items_count,
            "total": float(cart.total),
            "last_activity": cart.last_activity,
            "days_abandoned": (datetime.utcnow() - cart.last_activity).days
        }
        for cart in abandoned_carts
    ]