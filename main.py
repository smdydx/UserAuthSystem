"""
Main FastAPI application entry point
"""
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.routers import auth_simplified as auth, users, categories, products, discounts, cart, orders
from app.middleware.auth_middleware import AuthMiddleware
from app.utils.exceptions import CustomHTTPException
from app.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Authentication System",
    description="A comprehensive authentication system with JWT tokens and role-based access control",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom auth middleware
app.add_middleware(AuthMiddleware)

# Exception handlers
@app.exception_handler(CustomHTTPException)
async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
    """Handle custom HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_code": exc.error_code,
            "timestamp": exc.timestamp.isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )

# Include routers
auth_router = auth.router
user_router = users.router
category_router = categories.router
product_router = products.router
discount_router = discounts.router
cart_router = cart.router
order_router = orders.router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(category_router, prefix="/api/v1", tags=["Categories & Tags"])
app.include_router(product_router, prefix="/api/v1", tags=["Products"])
app.include_router(discount_router, prefix="/api/v1", tags=["Discounts"])
app.include_router(cart_router, prefix="/api/v1", tags=["Cart & Wishlist"])
app.include_router(order_router, prefix="/api/v1", tags=["Orders & Checkout"])

# Admin router
from app.routers import admin
admin_router = admin.router
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "FastAPI Authentication Service is running"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FastAPI Authentication System",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )