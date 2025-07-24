# Product Management API Documentation

## Overview

Complete e-commerce product management system with advanced features including variants, categories, pricing rules, and image handling.

## Features Implemented

### ✅ CRUD APIs for Products
- Complete product lifecycle management
- SKU and slug-based unique identification
- Status management (draft, active, inactive, out_of_stock, discontinued)
- Featured product support
- Digital and physical product handling

### ✅ Category & Subcategory Management
- Hierarchical category structure
- SEO optimization (meta tags, descriptions, keywords)
- Category slug system for clean URLs
- Active/inactive status management

### ✅ Product Variants System
- Size, color, and custom attribute variants
- Individual SKU tracking per variant
- Separate pricing and inventory per variant
- Variant-specific images
- JSON-based flexible option storage

### ✅ Image Upload Support
- Local image processing and optimization
- Automatic resizing (max 2048x2048)
- Format conversion (JPEG, PNG, WebP)
- Primary image designation
- Alt text and metadata support
- **Ready for Cloudinary/S3 integration** (placeholder services included)

### ✅ Discount & Pricing Rules
- Percentage and fixed-amount discounts
- Minimum quantity requirements
- Minimum purchase amount conditions
- Usage limits and tracking
- Time-based validity (start/end dates)
- Automatic best discount calculation

### ✅ SEO Fields
- Product and category slugs for clean URLs
- Meta titles, descriptions, and keywords
- Search engine optimization ready
- Automatic slug generation from names

### ✅ Product Tags
- Flexible tagging system
- Color-coded tags for organization
- Tag-based product filtering
- Many-to-many relationship support

## API Endpoints Summary

### Categories & Tags
```
POST   /api/v1/categories              # Create category
GET    /api/v1/categories              # List categories
GET    /api/v1/categories/main         # Get main categories
GET    /api/v1/categories/{id}         # Get category by ID
GET    /api/v1/categories/slug/{slug}  # Get category by slug
PUT    /api/v1/categories/{id}         # Update category
DELETE /api/v1/categories/{id}         # Delete category

POST   /api/v1/tags                    # Create product tag
GET    /api/v1/tags                    # List tags
GET    /api/v1/tags/{id}               # Get tag by ID
GET    /api/v1/tags/slug/{slug}        # Get tag by slug
PUT    /api/v1/tags/{id}               # Update tag
DELETE /api/v1/tags/{id}               # Delete tag
```

### Products
```
POST   /api/v1/products                        # Create product
GET    /api/v1/products                        # List products (paginated, filtered)
GET    /api/v1/products/featured               # Get featured products
GET    /api/v1/products/search                 # Search products
GET    /api/v1/products/category/{category_id} # Get products by category
GET    /api/v1/products/{id}                   # Get product by ID
GET    /api/v1/products/slug/{slug}            # Get product by slug
PUT    /api/v1/products/{id}                   # Update product
DELETE /api/v1/products/{id}                   # Delete product
```

### Product Images
```
POST   /api/v1/products/{id}/images            # Add product image
DELETE /api/v1/products/images/{image_id}      # Delete image
PUT    /api/v1/products/{id}/images/{image_id}/primary # Set primary image
```

### Product Variants
```
POST   /api/v1/products/{id}/variants          # Create variant
GET    /api/v1/products/{id}/variants          # Get product variants
GET    /api/v1/variants/{id}                   # Get variant by ID
PUT    /api/v1/variants/{id}                   # Update variant
PUT    /api/v1/variants/{id}/inventory         # Update variant inventory
DELETE /api/v1/variants/{id}                   # Delete variant

POST   /api/v1/variant-options                 # Create variant option
GET    /api/v1/variant-options                 # List variant options
GET    /api/v1/variant-options/names           # Get option names (Color, Size, etc.)
DELETE /api/v1/variant-options/{id}            # Delete variant option
```

### Discounts & Pricing
```
POST   /api/v1/products/{id}/discounts         # Create product discount
GET    /api/v1/products/{id}/discounts         # Get product discounts
GET    /api/v1/discounts/{id}                  # Get discount by ID
PUT    /api/v1/discounts/{id}                  # Update discount
DELETE /api/v1/discounts/{id}                  # Delete discount
GET    /api/v1/products/{id}/price             # Calculate discounted price
```

## Database Schema

### Core Tables
- **products** - Main product information
- **categories** - Product categories with hierarchy
- **product_images** - Product image management
- **product_variants** - Product size/color variants
- **variant_options** - Available variant options
- **product_discounts** - Pricing rules and discounts
- **product_tags** - Product tagging system
- **product_tag_associations** - Many-to-many product-tag relationship

### Key Features
- **Inventory Tracking**: Individual inventory per product and variant
- **SEO Optimization**: Slugs, meta tags for all entities
- **Flexible Variants**: JSON-based option storage
- **Image Management**: Multiple images per product with primary designation
- **Discount Engine**: Automatic best price calculation
- **Search & Filter**: Advanced filtering and full-text search

## Usage Examples

### Creating a Product with Variants
```json
{
  "name": "Premium T-Shirt",
  "sku": "TSHIRT-001",
  "price": 29.99,
  "description": "High-quality cotton t-shirt",
  "category_id": 1,
  "status": "active",
  "variants": [
    {
      "sku": "TSHIRT-001-S-RED",
      "title": "Small / Red",
      "options": {"Size": "Small", "Color": "Red"},
      "inventory_quantity": 10
    },
    {
      "sku": "TSHIRT-001-M-RED", 
      "title": "Medium / Red",
      "options": {"Size": "Medium", "Color": "Red"},
      "inventory_quantity": 15
    }
  ],
  "images": [
    {
      "url": "https://example.com/tshirt-red.jpg",
      "alt_text": "Red Premium T-Shirt",
      "is_primary": true
    }
  ]
}
```

### Advanced Product Search
```
GET /api/v1/products?category_id=1&min_price=10&max_price=50&in_stock=true&search=shirt&sort_by=price&sort_order=asc
```

## Security

- **Admin Only**: Create, update, delete operations require admin role
- **Public Read**: Product browsing available to all users
- **Authentication**: JWT-based authentication for protected operations

## Integration Ready

### Image Upload Services
- **Local Storage**: Implemented with automatic optimization
- **Cloudinary**: Service placeholder ready for integration
- **AWS S3**: Service placeholder ready for integration

### External Features Ready
- **Payment Integration**: Discount calculations ready for checkout
- **Inventory Management**: Real-time stock tracking
- **Search Engine**: SEO fields ready for indexing
- **Mobile Apps**: RESTful APIs ready for any frontend

## Testing

Use the interactive API documentation at:
- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

All endpoints are fully documented with request/response schemas and examples.