
"""
Admin Analytics Schemas
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from decimal import Decimal


class DashboardStats(BaseModel):
    """Dashboard statistics response"""
    users: Dict[str, Any]
    products: Dict[str, Any]
    orders: Dict[str, Any]
    revenue: Dict[str, Any]
    carts: Dict[str, Any]


class SalesAnalytics(BaseModel):
    """Sales analytics response"""
    period: str
    data: List[Dict[str, Any]]
    summary: Dict[str, Any]


class TopProductsAnalytics(BaseModel):
    """Top products analytics"""
    product_id: int
    product_name: str
    total_quantity: int
    total_revenue: Decimal
    orders_count: int
    avg_price: Decimal


class UserAnalytics(BaseModel):
    """User analytics response"""
    registration_trends: List[Dict[str, Any]]
    role_distribution: List[Dict[str, Any]]
    top_customers: List[Dict[str, Any]]


class OrderAnalytics(BaseModel):
    """Order analytics response"""
    total_orders: int
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    completion_rate: float
    avg_processing_time: float


class RevenueAnalytics(BaseModel):
    """Revenue analytics response"""
    total_revenue: Decimal
    monthly_revenue: List[Dict[str, Any]]
    top_revenue_sources: List[Dict[str, Any]]
    revenue_growth: float


class ExportRequest(BaseModel):
    """Export request schema"""
    export_type: str  # 'orders', 'products', 'users'
    format: str = "csv"  # 'csv', 'excel'
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None


class ProductPerformance(BaseModel):
    """Product performance analytics"""
    product_id: int
    product_name: str
    category: str
    total_sold: int
    revenue: Decimal
    profit_margin: float
    stock_status: str
    performance_score: float


class RegionAnalytics(BaseModel):
    """Regional analytics"""
    region: str
    orders_count: int
    revenue: Decimal
    top_products: List[str]
    avg_order_value: Decimal


class AdminPermissionCheck(BaseModel):
    """Admin permission verification"""
    user_id: int
    action: str
    resource: str
    allowed: bool
    reason: Optional[str] = None
