# FastAPI Authentication System

## Overview

This is a comprehensive FastAPI-based authentication system featuring JWT token authentication, role-based access control, email verification, password reset functionality, and user management. The application follows a clean architecture pattern with separate layers for models, services, routers, and utilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: FastAPI with Python
- **Architecture Pattern**: Layered architecture with separation of concerns
- **API Design**: RESTful APIs with OpenAPI documentation
- **Authentication**: JWT-based authentication with access and refresh tokens
- **Authorization**: Role-based access control (RBAC) with middleware

### Database Architecture
- **ORM**: SQLAlchemy with declarative base models
- **Migration Tool**: Alembic for database schema versioning
- **Default Database**: SQLite (configurable via DATABASE_URL)
- **Session Management**: SQLAlchemy sessions with dependency injection

### Security Architecture
- **Password Hashing**: Bcrypt via Passlib
- **JWT Tokens**: Jose library for token creation and verification
- **Password Validation**: Configurable complexity requirements
- **Token Types**: Access tokens, refresh tokens, email verification tokens, password reset tokens

## Key Components

### Authentication & Authorization
- **JWT Middleware**: Custom middleware (`AuthMiddleware`) for token validation
- **Dependencies**: FastAPI dependencies for user authentication and role checking
- **Token Management**: Separate models for different token types with expiration tracking
- **Role System**: Enum-based roles (customer, admin, vendor) with hierarchical permissions

### User Management
- **User Model**: Complete user entity with status tracking, timestamps, and relationships
- **User Service**: Business logic for user operations (CRUD, search, statistics)
- **Profile Management**: User profile updates and password changes

### Email System
- **Email Service**: SMTP-based email sending with HTML/text support
- **Email Types**: Verification emails, password reset emails, welcome emails
- **Template System**: HTML email templates with dynamic content

### Error Handling
- **Custom Exceptions**: Structured error classes with error codes and timestamps
- **Global Exception Handler**: Centralized error response formatting
- **Validation Errors**: Pydantic-based request validation with detailed error messages

## Data Flow

### Authentication Flow
1. User registration → Password validation → Email verification token generation → Welcome email
2. User login → Credentials verification → JWT token generation → Session creation
3. Request authentication → Middleware token validation → User context injection
4. Token refresh → Refresh token validation → New access token generation

### Authorization Flow
1. Protected endpoint access → Current user extraction → Role verification → Request processing
2. Admin operations → Admin role requirement → Resource access → Response

### Email Verification Flow
1. Registration/request → Verification token creation → Email sending → Token validation → Account verification

### Password Reset Flow
1. Reset request → User validation → Reset token creation → Email sending → Token validation → Password update

## External Dependencies

### Core Dependencies
- **FastAPI**: Web framework with automatic API documentation
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration management
- **Pydantic**: Data validation and serialization
- **Passlib**: Password hashing with bcrypt
- **python-jose**: JWT token handling

### Email Dependencies
- **SMTP**: Email delivery via configurable SMTP servers
- **SSL/TLS**: Secure email transmission

### Development Dependencies
- **Uvicorn**: ASGI server for development and production
- **Python-multipart**: Form data handling
- **Python-dotenv**: Environment variable management

## Deployment Strategy

### Configuration Management
- **Environment Variables**: All sensitive configuration via environment variables
- **Settings Class**: Pydantic-based configuration with validation and defaults
- **Multi-environment Support**: Development, staging, and production configurations

### Database Strategy
- **Migration System**: Alembic for schema version control
- **Connection Pooling**: SQLAlchemy engine with configurable pool settings
- **Database URL**: Flexible database backend support (SQLite, PostgreSQL, MySQL)

### Security Considerations
- **Secret Management**: Secure secret key generation and storage
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Token Security**: Secure token generation with expiration and revocation
- **Password Security**: Strong password requirements and secure hashing

### Logging & Monitoring
- **Structured Logging**: Configurable logging with colored console output
- **Log Rotation**: File-based logging with size limits and rotation
- **Error Tracking**: Comprehensive error logging with stack traces
- **Performance Monitoring**: Request/response logging for performance analysis

### Scalability Features
- **Stateless Design**: JWT-based authentication for horizontal scaling
- **Database Abstraction**: ORM-based data access for database portability
- **Service Layer**: Modular business logic for easy testing and maintenance
- **Dependency Injection**: FastAPI's dependency system for loose coupling

## Recent Changes: Latest modifications with dates

### July 15, 2025 - E-commerce API Cleanup & Simplification
- **API Cleanup**: Removed duplicate and unnecessary authentication endpoints
- **Simplified OTP System**: Unified password reset to single OTP-based flow
- **E-commerce Ready**: Streamlined to 7 core endpoints for e-commerce use
- **Simple Email OTP**: Added console-based OTP for development, Gmail-ready for production
- **Clean Architecture**: Replaced complex auth router with simplified version
- **Real-time Email**: Prepared system for Gmail SMTP integration
- **Unified Flow**: Single `/send-reset-otp` and `/reset-password-otp` endpoints

### July 14, 2025 - Advanced Security Features Implementation
- **SMS OTP Support**: Added Twilio integration for SMS-based OTP password reset
- **Rate Limiting**: Implemented rate limiting for OTP requests (3 per hour) and login attempts (10 per hour)  
- **User Account Lockout**: Added automatic account lockout after 5 failed login attempts (30-minute lockout)
- **Enhanced Security Models**: Created RateLimit and UserLockout database models
- **Phone Number Support**: Added phone_number field to User model and schemas
- **Security Services**: Implemented RateLimitService for comprehensive security management
- **Bank-Level Security**: Complete protection against brute force attacks and abuse