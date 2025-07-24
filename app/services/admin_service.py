
"""
Admin Service for Analytics and Management
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, extract, case
from datetime import datetime, timedelta
import csv
import io
import json
from decimal import Decimal

from app.models.user import User, UserRole
from app.models.product import Product, ProductStatus
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.schemas.admin import (
    DashboardStats, SalesAnalytics, TopProductsAnalytics, 
    UserAnalytics, OrderAnalytics, RevenueAnalytics
)


class AdminService:
    """Admin service for analytics and management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ===============================
    # DASHBOARD STATS
    # ===============================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        
        # Date ranges
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        last_30_days = datetime.utcnow() - timedelta(days=30)
        last_7_days = datetime.utcnow() - timedelta(days=7)
        
        # User Statistics
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        new_users_today = self.db.query(User).filter(
            func.date(User.created_at) == today
        ).count()
        
        # Product Statistics  
        total_products = self.db.query(Product).count()
        active_products = self.db.query(Product).filter(
            Product.status == ProductStatus.ACTIVE
        ).count()
        out_of_stock = self.db.query(Product).filter(
            Product.stock_quantity <= 0
        ).count()
        
        # Order Statistics
        total_orders = self.db.query(Order).count()
        pending_orders = self.db.query(Order).filter(
            Order.status == OrderStatus.PENDING
        ).count()
        orders_today = self.db.query(Order).filter(
            func.date(Order.created_at) == today
        ).count()
        
        # Revenue Statistics
        total_revenue = self.db.query(func.sum(Order.total)).filter(
            Order.payment_status == PaymentStatus.PAID
        ).scalar() or 0
        
        revenue_today = self.db.query(func.sum(Order.total)).filter(
            and_(
                func.date(Order.created_at) == today,
                Order.payment_status == PaymentStatus.PAID
            )
        ).scalar() or 0
        
        revenue_yesterday = self.db.query(func.sum(Order.total)).filter(
            and_(
                func.date(Order.created_at) == yesterday,
                Order.payment_status == PaymentStatus.PAID
            )
        ).scalar() or 0
        
        # Growth Calculations
        revenue_growth = 0
        if revenue_yesterday > 0:
            revenue_growth = ((revenue_today - revenue_yesterday) / revenue_yesterday) * 100
        
        # Average Order Value
        avg_order_value = self.db.query(func.avg(Order.total)).filter(
            Order.payment_status == PaymentStatus.PAID
        ).scalar() or 0
        
        # Cart Statistics
        active_carts = self.db.query(Cart).filter(
            Cart.items_count > 0
        ).count()
        
        abandoned_carts = self.db.query(Cart).filter(
            and_(
                Cart.items_count > 0,
                Cart.last_activity < last_7_days
            )
        ).count()
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "new_today": new_users_today,
                "growth_rate": self._calculate_user_growth()
            },
            "products": {
                "total": total_products,
                "active": active_products,
                "out_of_stock": out_of_stock,
                "stock_alerts": out_of_stock
            },
            "orders": {
                "total": total_orders,
                "pending": pending_orders,
                "today": orders_today,
                "completion_rate": self._calculate_order_completion_rate()
            },
            "revenue": {
                "total": float(total_revenue),
                "today": float(revenue_today),
                "yesterday": float(revenue_yesterday),
                "growth": revenue_growth,
                "avg_order_value": float(avg_order_value)
            },
            "carts": {
                "active": active_carts,
                "abandoned": abandoned_carts,
                "abandonment_rate": (abandoned_carts / (active_carts + abandoned_carts) * 100) if (active_carts + abandoned_carts) > 0 else 0
            }
        }
    
    # ===============================
    # SALES ANALYTICS
    # ===============================
    
    def get_sales_analytics(self, period: str = "monthly", days: int = 30) -> Dict[str, Any]:
        """Get sales analytics for specified period"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        if period == "weekly":
            date_format = "%Y-%W"
            date_trunc = func.date_trunc('week', Order.created_at)
        elif period == "monthly":
            date_format = "%Y-%m"
            date_trunc = func.date_trunc('month', Order.created_at)
        elif period == "yearly":
            date_format = "%Y"
            date_trunc = func.date_trunc('year', Order.created_at)
        else:  # daily
            date_format = "%Y-%m-%d"
            date_trunc = func.date_trunc('day', Order.created_at)
        
        # Sales by period
        sales_data = self.db.query(
            date_trunc.label('period'),
            func.count(Order.id).label('orders'),
            func.sum(Order.total).label('revenue'),
            func.avg(Order.total).label('avg_order_value')
        ).filter(
            and_(
                Order.created_at >= start_date,
                Order.payment_status == PaymentStatus.PAID
            )
        ).group_by(date_trunc).order_by(date_trunc).all()
        
        # Format data
        formatted_data = []
        for row in sales_data:
            formatted_data.append({
                "period": row.period.strftime(date_format),
                "orders": row.orders,
                "revenue": float(row.revenue or 0),
                "avg_order_value": float(row.avg_order_value or 0)
            })
        
        # Summary statistics
        total_orders = sum(item['orders'] for item in formatted_data)
        total_revenue = sum(item['revenue'] for item in formatted_data)
        avg_revenue = total_revenue / len(formatted_data) if formatted_data else 0
        
        return {
            "period": period,
            "data": formatted_data,
            "summary": {
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "avg_revenue_per_period": avg_revenue,
                "periods_count": len(formatted_data)
            }
        }
    
    # ===============================
    # TOP PRODUCTS ANALYTICS
    # ===============================
    
    def get_top_products(self, limit: int = 10, period_days: int = 30) -> List[Dict[str, Any]]:
        """Get top performing products"""
        
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        top_products = self.db.query(
            OrderItem.product_id,
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.final_price * OrderItem.quantity).label('total_revenue'),
            func.count(func.distinct(OrderItem.order_id)).label('orders_count'),
            func.avg(OrderItem.final_price).label('avg_price')
        ).join(Order).filter(
            and_(
                Order.created_at >= start_date,
                Order.payment_status == PaymentStatus.PAID
            )
        ).group_by(
            OrderItem.product_id, OrderItem.product_name
        ).order_by(
            desc(func.sum(OrderItem.final_price * OrderItem.quantity))
        ).limit(limit).all()
        
        result = []
        for product in top_products:
            result.append({
                "product_id": product.product_id,
                "product_name": product.product_name,
                "total_quantity": product.total_quantity,
                "total_revenue": float(product.total_revenue),
                "orders_count": product.orders_count,
                "avg_price": float(product.avg_price)
            })
        
        return result
    
    # ===============================
    # USER ANALYTICS
    # ===============================
    
    def get_user_analytics(self) -> Dict[str, Any]:
        """Get comprehensive user analytics"""
        
        # User registration trends (last 30 days)
        last_30_days = datetime.utcnow() - timedelta(days=30)
        
        registration_trends = self.db.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('registrations')
        ).filter(
            User.created_at >= last_30_days
        ).group_by(
            func.date(User.created_at)
        ).order_by(
            func.date(User.created_at)
        ).all()
        
        # Users by role
        role_distribution = self.db.query(
            User.role,
            func.count(User.id).label('count')
        ).group_by(User.role).all()
        
        # Top customers by orders
        top_customers = self.db.query(
            User.id,
            User.full_name,
            User.email,
            func.count(Order.id).label('orders_count'),
            func.sum(Order.total).label('total_spent')
        ).join(Order).filter(
            Order.payment_status == PaymentStatus.PAID
        ).group_by(
            User.id, User.full_name, User.email
        ).order_by(
            desc(func.sum(Order.total))
        ).limit(10).all()
        
        return {
            "registration_trends": [
                {
                    "date": trend.date.isoformat(),
                    "registrations": trend.registrations
                }
                for trend in registration_trends
            ],
            "role_distribution": [
                {
                    "role": role.role,
                    "count": role.count
                }
                for role in role_distribution
            ],
            "top_customers": [
                {
                    "user_id": customer.id,
                    "name": customer.full_name,
                    "email": customer.email,
                    "orders_count": customer.orders_count,
                    "total_spent": float(customer.total_spent or 0)
                }
                for customer in top_customers
            ]
        }
    
    # ===============================
    # EXPORT FUNCTIONALITY
    # ===============================
    
    def export_orders_csv(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> str:
        """Export orders to CSV format"""
        
        query = self.db.query(Order).options()
        
        if start_date:
            query = query.filter(Order.created_at >= start_date)
        if end_date:
            query = query.filter(Order.created_at <= end_date)
        
        orders = query.order_by(desc(Order.created_at)).all()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'Order Number', 'User Email', 'Status', 'Payment Status',
            'Subtotal', 'Tax', 'Shipping', 'Total', 'Items Count',
            'Created At', 'Shipped At', 'Delivered At'
        ])
        
        # Data rows
        for order in orders:
            writer.writerow([
                order.order_number,
                order.user.email if order.user else order.guest_email,
                order.status,
                order.payment_status,
                float(order.subtotal),
                float(order.tax_amount),
                float(order.shipping_cost),
                float(order.total),
                len(order.items),
                order.created_at.isoformat(),
                order.shipped_at.isoformat() if order.shipped_at else '',
                order.delivered_at.isoformat() if order.delivered_at else ''
            ])
        
        return output.getvalue()
    
    def export_products_csv(self) -> str:
        """Export products to CSV format"""
        
        products = self.db.query(Product).order_by(Product.name).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Name', 'SKU', 'Category', 'Price', 'Stock',
            'Status', 'Featured', 'Created At', 'Updated At'
        ])
        
        # Data rows
        for product in products:
            writer.writerow([
                product.id,
                product.name,
                product.sku,
                product.category.name if product.category else '',
                float(product.price),
                product.stock_quantity,
                product.status,
                product.is_featured,
                product.created_at.isoformat(),
                product.updated_at.isoformat()
            ])
        
        return output.getvalue()
    
    def export_users_csv(self) -> str:
        """Export users to CSV format"""
        
        users = self.db.query(User).order_by(User.created_at).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Email', 'Full Name', 'Role', 'Active',
            'Verified', 'Created At', 'Last Login'
        ])
        
        # Data rows
        for user in users:
            writer.writerow([
                user.id,
                user.email,
                user.full_name,
                user.role,
                user.is_active,
                user.is_verified,
                user.created_at.isoformat(),
                user.last_login.isoformat() if user.last_login else ''
            ])
        
        return output.getvalue()
    
    # ===============================
    # HELPER METHODS
    # ===============================
    
    def _calculate_user_growth(self) -> float:
        """Calculate user growth rate (last 30 days vs previous 30 days)"""
        
        today = datetime.utcnow().date()
        last_30_days = today - timedelta(days=30)
        last_60_days = today - timedelta(days=60)
        
        current_period = self.db.query(User).filter(
            User.created_at >= last_30_days
        ).count()
        
        previous_period = self.db.query(User).filter(
            and_(
                User.created_at >= last_60_days,
                User.created_at < last_30_days
            )
        ).count()
        
        if previous_period == 0:
            return 100.0 if current_period > 0 else 0.0
        
        return ((current_period - previous_period) / previous_period) * 100
    
    def _calculate_order_completion_rate(self) -> float:
        """Calculate order completion rate"""
        
        total_orders = self.db.query(Order).count()
        completed_orders = self.db.query(Order).filter(
            Order.status == OrderStatus.DELIVERED
        ).count()
        
        if total_orders == 0:
            return 0.0
        
        return (completed_orders / total_orders) * 100
