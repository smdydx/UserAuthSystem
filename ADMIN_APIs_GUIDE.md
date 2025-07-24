
# 🔧 Admin APIs & Analytics Guide

## 🎯 Complete Admin Management System

यह comprehensive admin system है जो आपको complete control देता है:

### ✅ **Dashboard Analytics**
- Real-time statistics और metrics
- User, product, order, revenue analytics
- Growth rates और performance indicators
- Cart abandonment tracking

### ✅ **Sales Analytics** 
- Daily/Weekly/Monthly/Yearly reports
- Revenue trends और comparison
- Top performing products
- Customer purchase patterns

### ✅ **Export Functionality**
- CSV/Excel export for orders, products, users
- Custom date range filtering
- Bulk data download capabilities

### ✅ **User Management**
- Complete user CRUD operations
- Role management (Admin/Customer/Vendor)
- User suspension और activation
- Registration trends tracking

### ✅ **Product Management**
- Product performance analytics
- Low stock alerts
- Inventory tracking
- Sales performance metrics

### ✅ **Order Management**
- Pending orders queue
- Order status analytics
- Payment status tracking
- Processing time analysis

---

## 🚀 Admin API Endpoints

### **Dashboard & Analytics**
```bash
# Dashboard Statistics
GET /api/v1/admin/dashboard/stats

# Sales Analytics
GET /api/v1/admin/analytics/sales?period=monthly&days=30

# User Analytics
GET /api/v1/admin/analytics/users

# Top Products
GET /api/v1/admin/analytics/products/top?limit=10

# Revenue Analytics
GET /api/v1/admin/analytics/revenue?period=monthly
```

### **Export & Reports**
```bash
# Export Orders
POST /api/v1/admin/export/orders?format=csv

# Export Products  
POST /api/v1/admin/export/products?format=csv

# Export Users
POST /api/v1/admin/export/users?format=csv
```

### **User Management**
```bash
# Get All Users
GET /api/v1/admin/users?search=john&role=customer

# Update User Role
PUT /api/v1/admin/users/{user_id}/role?new_role=admin

# Suspend User
POST /api/v1/admin/users/{user_id}/suspend?reason=violation
```

### **Product Management**
```bash
# Product Performance
GET /api/v1/admin/products/performance?limit=20&sort_by=revenue

# Low Stock Products
GET /api/v1/admin/products/low-stock?threshold=10
```

### **Order Management**
```bash
# Pending Orders
GET /api/v1/admin/orders/pending?limit=50

# Order Analytics
GET /api/v1/admin/orders/analytics?period_days=30
```

### **System Health**
```bash
# System Health Check
GET /api/v1/admin/system/health

# System Logs
GET /api/v1/admin/system/logs?level=INFO&limit=100
```

---

## 📊 Dashboard Response Example

```json
{
  "users": {
    "total": 1250,
    "active": 1180,
    "new_today": 15,
    "growth_rate": 12.5
  },
  "products": {
    "total": 856,
    "active": 820,
    "out_of_stock": 25,
    "stock_alerts": 25
  },
  "orders": {
    "total": 3450,
    "pending": 45,
    "today": 67,
    "completion_rate": 89.5
  },
  "revenue": {
    "total": 2850000.50,
    "today": 45600.25,
    "yesterday": 38900.75,
    "growth": 17.2,
    "avg_order_value": 826.09
  },
  "carts": {
    "active": 234,
    "abandoned": 89,
    "abandonment_rate": 27.5
  }
}
```

---

## 🔐 Security Features

### **Role-Based Access Control**
```python
# All admin endpoints protected with:
current_user: User = Depends(require_admin)

# Automatic permission checking
# Only admins can access admin APIs
```

### **Action Logging**
- सभी admin actions logged
- User role changes tracked
- Export activities monitored
- Security audit trail

### **Rate Limiting**
- Admin APIs rate limited
- Bulk export restrictions
- API abuse prevention

---

## 📈 Analytics Features

### **Real-time Metrics**
- Live dashboard updates
- Real-time order tracking
- Instant stock alerts
- Performance monitoring

### **Trend Analysis**
- Revenue growth tracking
- User acquisition trends
- Product performance analysis
- Seasonal pattern detection

### **Comparison Reports**
- Period-over-period comparison
- Year-over-year analysis
- Benchmark performance
- Growth rate calculations

---

## 💾 Export Capabilities

### **CSV Exports**
```bash
# Orders Export
curl -X POST "http://localhost:5000/api/v1/admin/export/orders?format=csv" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Products Export  
curl -X POST "http://localhost:5000/api/v1/admin/export/products?format=csv" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### **Custom Filtering**
- Date range filtering
- Status-based filtering
- Category-wise exports
- User role filtering

---

## 🎨 Frontend Integration Ready

### **React Dashboard Example**
```javascript
// Dashboard Stats
const fetchDashboardStats = async () => {
  const response = await fetch('/api/v1/admin/dashboard/stats', {
    headers: { 'Authorization': `Bearer ${adminToken}` }
  });
  return response.json();
};

// Export Orders
const exportOrders = async () => {
  const response = await fetch('/api/v1/admin/export/orders?format=csv', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${adminToken}` }
  });
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'orders_export.csv';
  a.click();
};
```

---

## 🚀 **Ready Features**

### ✅ **Complete Admin System**
- Dashboard analytics
- User management  
- Product analytics
- Order management
- Export functionality
- Security controls

### ✅ **Production Ready**
- Role-based access control
- API rate limiting
- Error handling
- Data validation
- Security logging

### ✅ **Scalable Architecture**
- Service-based design
- Database optimization
- Caching ready
- Performance monitoring

---

## 🎯 **Test Admin APIs**

**Server running on**: `http://localhost:5000`

**API Documentation**: `http://localhost:5000/docs`

**All admin endpoints require admin authentication!** 🔐

आपका complete **Admin & Analytics System** ready है! 🎉 

Dashboard, reports, user management, product analytics - सब कुछ available है। Admin panel के लिए frontend integrate कर सकते हैं।
