
"""
Order Management API Routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import math

from app.core.database import get_db
from app.dependencies import get_current_user, get_current_active_user
from app.models.user import User
from app.models.order import OrderStatus, PaymentStatus
from app.services.order_service import OrderService
from app.schemas.order import (
    OrderCreate, OrderResponse, OrderSummary, OrderListResponse,
    OrderStatusUpdate, OrderRefundCreate, OrderRefundResponse,
    OrderSearchFilters, OrderAnalytics
)

router = APIRouter()

# ===============================
# ORDER MANAGEMENT ENDPOINTS
# ===============================

@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Create a new order from cart or items"""
    user_id = current_user.id if current_user else None
    
    # For guest orders, email is required
    if not user_id and not order_data.guest_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required for guest orders"
        )
    
    return OrderService.create_order(db, order_data, user_id)


@router.get("/orders", response_model=OrderListResponse)
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[OrderStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    order_number: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get orders with filtering and pagination"""
    
    filters = OrderSearchFilters(
        status=status,
        payment_status=payment_status,
        order_number=order_number
    )
    
    # Non-admin users can only see their own orders
    user_id = None if current_user.is_admin else current_user.id
    
    orders, total = OrderService.get_orders(db, filters, skip, limit, user_id)
    
    # Convert to summary format
    order_summaries = []
    for order in orders:
        order_summaries.append(OrderSummary(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            payment_status=order.payment_status,
            total=order.total,
            items_count=len(order.items),
            created_at=order.created_at
        ))
    
    return OrderListResponse(
        orders=order_summaries,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=math.ceil(total / limit)
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get order details by ID"""
    
    # Non-admin users can only see their own orders
    user_id = None if current_user.is_admin else current_user.id
    
    order = OrderService.get_order(db, order_id, user_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.put("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update order status (Admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update order status"
        )
    
    return OrderService.update_order_status(db, order_id, status_update, current_user.id)


@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cancel order (Customer can cancel own orders, Admin can cancel any)"""
    
    # Get order first to check ownership
    user_id = None if current_user.is_admin else current_user.id
    order = OrderService.get_order(db, order_id, user_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if not order.can_be_cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order cannot be cancelled"
        )
    
    status_update = OrderStatusUpdate(
        status=OrderStatus.CANCELLED,
        reason=reason or "Cancelled by customer"
    )
    
    return OrderService.update_order_status(db, order_id, status_update, current_user.id)


# ===============================
# REFUND MANAGEMENT ENDPOINTS
# ===============================

@router.post("/orders/{order_id}/refund", response_model=OrderRefundResponse, status_code=status.HTTP_201_CREATED)
async def create_refund(
    order_id: int,
    refund_data: OrderRefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a refund request"""
    
    # Check if user owns the order (for non-admin users)
    if not current_user.is_admin:
        user_order = OrderService.get_order(db, order_id, current_user.id)
        if not user_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
    
    return OrderService.create_refund(db, order_id, refund_data, current_user.id)


@router.get("/orders/{order_id}/refunds", response_model=List[OrderRefundResponse])
async def get_order_refunds(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get refunds for an order"""
    
    # Check if user owns the order (for non-admin users)
    user_id = None if current_user.is_admin else current_user.id
    order = OrderService.get_order(db, order_id, user_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order.refunds


# ===============================
# ADMIN ANALYTICS ENDPOINTS
# ===============================

@router.get("/orders/analytics/summary", response_model=OrderAnalytics)
async def get_order_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get order analytics summary (Admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access analytics"
        )
    
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_
    from app.models.order import Order, OrderItem
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Basic statistics
    orders_query = db.query(Order).filter(Order.created_at >= start_date)
    
    total_orders = orders_query.count()
    total_revenue = orders_query.with_entities(func.sum(Order.total)).scalar() or 0
    
    # Status counts
    pending_orders = orders_query.filter(Order.status == OrderStatus.PENDING).count()
    completed_orders = orders_query.filter(Order.status == OrderStatus.DELIVERED).count()
    cancelled_orders = orders_query.filter(Order.status == OrderStatus.CANCELLED).count()
    refunded_orders = orders_query.filter(Order.status == OrderStatus.REFUNDED).count()
    
    # Average order value
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Top products
    top_products = (
        db.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.final_price * OrderItem.quantity).label('total_revenue')
        )
        .join(Order)
        .filter(Order.created_at >= start_date)
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
        .all()
    )
    
    top_products_list = [
        {
            "product_name": product.product_name,
            "total_quantity": product.total_quantity,
            "total_revenue": float(product.total_revenue)
        }
        for product in top_products
    ]
    
    return OrderAnalytics(
        total_orders=total_orders,
        total_revenue=total_revenue,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        refunded_orders=refunded_orders,
        average_order_value=avg_order_value,
        top_products=top_products_list
    )


@router.get("/orders/admin/pending", response_model=List[OrderSummary])
async def get_pending_orders(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get pending orders for admin review"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access this endpoint"
        )
    
    filters = OrderSearchFilters(status=OrderStatus.PENDING)
    orders, _ = OrderService.get_orders(db, filters, 0, limit)
    
    return [
        OrderSummary(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            payment_status=order.payment_status,
            total=order.total,
            items_count=len(order.items),
            created_at=order.created_at
        )
        for order in orders
    ]
