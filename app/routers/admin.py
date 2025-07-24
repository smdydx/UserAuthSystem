
"""
Admin Management and Analytics API Routes
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import io

from app.core.database import get_db
from app.dependencies import get_current_active_user, require_admin
from app.models.user import User, UserRole
from app.services.admin_service import AdminService
from app.services.user_service import UserService
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.schemas.admin import (
    DashboardStats, SalesAnalytics, UserAnalytics, ExportRequest,
    ProductPerformance, RegionAnalytics
)
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.product import ProductResponse, ProductUpdate
from app.schemas.order import OrderResponse, OrderStatusUpdate

router = APIRouter()

# ===============================
# DASHBOARD ANALYTICS
# ===============================

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get comprehensive dashboard statistics (Admin only)"""
    admin_service = AdminService(db)
    return admin_service.get_dashboard_stats()


@router.get("/analytics/sales")
async def get_sales_analytics(
    period: str = Query("monthly", regex="^(daily|weekly|monthly|yearly)$"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get sales analytics for specified period (Admin only)"""
    admin_service = AdminService(db)
    return admin_service.get_sales_analytics(period=period, days=days)


@router.get("/analytics/users")
async def get_user_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get user analytics and trends (Admin only)"""
    admin_service = AdminService(db)
    return admin_service.get_user_analytics()


@router.get("/analytics/products/top")
async def get_top_products(
    limit: int = Query(10, ge=1, le=50),
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get top performing products (Admin only)"""
    admin_service = AdminService(db)
    return admin_service.get_top_products(limit=limit, period_days=period_days)


@router.get("/analytics/revenue")
async def get_revenue_analytics(
    period: str = Query("monthly", regex="^(daily|weekly|monthly|yearly)$"),
    comparison_period: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get revenue analytics with optional comparison (Admin only)"""
    admin_service = AdminService(db)
    
    # Get current period data
    current_data = admin_service.get_sales_analytics(period=period)
    
    if comparison_period:
        # Get previous period for comparison
        if period == "daily":
            days = 30
        elif period == "weekly":
            days = 14
        elif period == "monthly":
            days = 60
        else:  # yearly
            days = 730
        
        previous_data = admin_service.get_sales_analytics(period=period, days=days)
        
        return {
            "current_period": current_data,
            "previous_period": previous_data,
            "comparison": True
        }
    
    return current_data


# ===============================
# EXPORT FUNCTIONALITY
# ===============================

@router.post("/export/orders")
async def export_orders(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    format: str = Query("csv", regex="^(csv|excel)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Export orders data (Admin only)"""
    admin_service = AdminService(db)
    
    if format == "csv":
        csv_content = admin_service.export_orders_csv(start_date, end_date)
        
        # Create file response
        output = io.StringIO(csv_content)
        response = StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = "attachment; filename=orders_export.csv"
        return response
    
    # Excel export would be implemented here
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Excel export not yet implemented"
    )


@router.post("/export/products")
async def export_products(
    format: str = Query("csv", regex="^(csv|excel)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Export products data (Admin only)"""
    admin_service = AdminService(db)
    
    if format == "csv":
        csv_content = admin_service.export_products_csv()
        
        response = StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = "attachment; filename=products_export.csv"
        return response
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Excel export not yet implemented"
    )


@router.post("/export/users")
async def export_users(
    format: str = Query("csv", regex="^(csv|excel)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Export users data (Admin only)"""
    admin_service = AdminService(db)
    
    if format == "csv":
        csv_content = admin_service.export_users_csv()
        
        response = StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = "attachment; filename=users_export.csv"
        return response
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Excel export not yet implemented"
    )


# ===============================
# USER MANAGEMENT
# ===============================

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all users with advanced filtering (Admin only)"""
    user_service = UserService(db)
    
    # Apply additional filtering
    query = db.query(User)
    
    if search:
        query = query.filter(
            or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.offset(skip).limit(limit).all()
    return users


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update user role (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent removing last admin
    if user.role == UserRole.ADMIN and new_role != UserRole.ADMIN:
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last admin user"
            )
    
    user.role = new_role
    db.commit()
    
    return {"message": f"User role updated to {new_role}", "user_id": user_id}


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Suspend user account (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot suspend your own account"
        )
    
    user.is_active = False
    db.commit()
    
    # Log suspension (implement logging service if needed)
    
    return {"message": "User suspended successfully", "reason": reason}


# ===============================
# PRODUCT MANAGEMENT
# ===============================

@router.get("/products/performance")
async def get_product_performance(
    limit: int = Query(20, ge=1, le=100),
    period_days: int = Query(30, ge=1, le=365),
    sort_by: str = Query("revenue", regex="^(revenue|quantity|orders)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get product performance analytics (Admin only)"""
    from sqlalchemy import func, desc
    from app.models.order import OrderItem, Order, PaymentStatus
    from app.models.product import Product
    
    start_date = datetime.utcnow() - timedelta(days=period_days)
    
    # Base query for product performance
    query = db.query(
        Product.id,
        Product.name,
        Product.sku,
        Product.stock_quantity,
        func.coalesce(func.sum(OrderItem.quantity), 0).label('total_sold'),
        func.coalesce(func.sum(OrderItem.final_price * OrderItem.quantity), 0).label('revenue'),
        func.count(func.distinct(OrderItem.order_id)).label('orders_count')
    ).outerjoin(OrderItem, Product.id == OrderItem.product_id)\
     .outerjoin(Order, OrderItem.order_id == Order.id)\
     .filter(
         or_(
             Order.created_at.is_(None),
             and_(
                 Order.created_at >= start_date,
                 Order.payment_status == PaymentStatus.PAID
             )
         )
     ).group_by(Product.id, Product.name, Product.sku, Product.stock_quantity)
    
    # Apply sorting
    if sort_by == "revenue":
        query = query.order_by(desc('revenue'))
    elif sort_by == "quantity":
        query = query.order_by(desc('total_sold'))
    else:  # orders
        query = query.order_by(desc('orders_count'))
    
    products = query.limit(limit).all()
    
    return [
        {
            "product_id": p.id,
            "product_name": p.name,
            "sku": p.sku,
            "stock_quantity": p.stock_quantity,
            "total_sold": p.total_sold,
            "revenue": float(p.revenue),
            "orders_count": p.orders_count,
            "stock_status": "low" if p.stock_quantity < 10 else "normal"
        }
        for p in products
    ]


@router.get("/products/low-stock")
async def get_low_stock_products(
    threshold: int = Query(10, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get products with low stock (Admin only)"""
    from app.models.product import Product, ProductStatus
    
    low_stock_products = db.query(Product).filter(
        and_(
            Product.stock_quantity <= threshold,
            Product.status == ProductStatus.ACTIVE
        )
    ).order_by(Product.stock_quantity).all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "current_stock": p.stock_quantity,
            "status": p.status,
            "category": p.category.name if p.category else None
        }
        for p in low_stock_products
    ]


# ===============================
# ORDER MANAGEMENT
# ===============================

@router.get("/orders/pending")
async def get_pending_orders(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get pending orders for admin review (Admin only)"""
    from app.models.order import Order, OrderStatus
    
    pending_orders = db.query(Order).filter(
        Order.status == OrderStatus.PENDING
    ).order_by(Order.created_at).limit(limit).all()
    
    return [
        {
            "id": order.id,
            "order_number": order.order_number,
            "customer_email": order.user.email if order.user else order.guest_email,
            "total": float(order.total),
            "items_count": len(order.items),
            "created_at": order.created_at,
            "payment_status": order.payment_status
        }
        for order in pending_orders
    ]


@router.get("/orders/analytics")
async def get_order_analytics(
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get comprehensive order analytics (Admin only)"""
    from app.models.order import Order, OrderStatus, PaymentStatus
    
    start_date = datetime.utcnow() - timedelta(days=period_days)
    
    # Order status distribution
    status_distribution = db.query(
        Order.status,
        func.count(Order.id).label('count')
    ).filter(
        Order.created_at >= start_date
    ).group_by(Order.status).all()
    
    # Payment status distribution
    payment_distribution = db.query(
        Order.payment_status,
        func.count(Order.id).label('count')
    ).filter(
        Order.created_at >= start_date
    ).group_by(Order.payment_status).all()
    
    # Daily order trends
    daily_orders = db.query(
        func.date(Order.created_at).label('date'),
        func.count(Order.id).label('orders'),
        func.sum(Order.total).label('revenue')
    ).filter(
        Order.created_at >= start_date
    ).group_by(
        func.date(Order.created_at)
    ).order_by(
        func.date(Order.created_at)
    ).all()
    
    return {
        "status_distribution": [
            {"status": status.status, "count": status.count}
            for status in status_distribution
        ],
        "payment_distribution": [
            {"payment_status": payment.payment_status, "count": payment.count}
            for payment in payment_distribution
        ],
        "daily_trends": [
            {
                "date": day.date.isoformat(),
                "orders": day.orders,
                "revenue": float(day.revenue or 0)
            }
            for day in daily_orders
        ]
    }


# ===============================
# SYSTEM HEALTH & MONITORING
# ===============================

@router.get("/system/health")
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get system health status (Admin only)"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        
        # Get system statistics
        from app.models.user import User
        from app.models.product import Product
        from app.models.order import Order
        
        user_count = db.query(User).count()
        product_count = db.query(Product).count()
        order_count = db.query(Order).count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "statistics": {
                "total_users": user_count,
                "total_products": product_count,
                "total_orders": order_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/system/logs")
async def get_system_logs(
    limit: int = Query(100, ge=1, le=1000),
    level: str = Query("INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get system logs (Admin only)"""
    # This would integrate with your logging system
    # For now, return a placeholder response
    
    return {
        "message": "Log retrieval not yet implemented",
        "suggestion": "Implement integration with your logging system"
    }
