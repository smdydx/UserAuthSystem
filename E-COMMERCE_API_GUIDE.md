# E-commerce Authentication API Guide

## Clean & Simple APIs for E-commerce Projects

This FastAPI authentication system has been optimized for e-commerce use with only **7 essential endpoints**.

### 🔐 Core Authentication Endpoints

#### 1. **POST /api/v1/auth/register**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "phone_number": "+1234567890"
}
```

#### 2. **POST /api/v1/auth/login**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```
**Returns:** JWT access token and refresh token

#### 3. **POST /api/v1/auth/refresh**
```json
{
  "refresh_token": "your_refresh_token_here"
}
```

#### 4. **POST /api/v1/auth/logout**
```json
{
  "refresh_token": "your_refresh_token_here"
}
```

### 🔄 Password Reset (OTP-based)

#### 5. **POST /api/v1/auth/send-reset-otp**
```json
{
  "email": "user@example.com",
  "method": "email"
}
```
**Methods:** `"email"` or `"sms"`

#### 6. **POST /api/v1/auth/reset-password-otp**
```json
{
  "email": "user@example.com",
  "otp_code": "123456",
  "new_password": "NewSecurePass123!"
}
```

### 👤 User Profile

#### 7. **GET /api/v1/auth/me**
**Headers:** `Authorization: Bearer your_access_token`

---

## 📧 Email Configuration

### For Development (Console Output)
OTP codes are printed to console - perfect for testing!

### For Production (Gmail)
Set these environment variables:
```bash
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

**Gmail Setup:**
1. Go to Google Account → Security
2. Enable 2-factor authentication
3. Go to "App passwords"
4. Create password for "Mail"
5. Use this password (not your regular Gmail password)

---

## 🔒 Security Features

✅ **Rate Limiting**: Prevents brute force attacks
✅ **Account Lockout**: Auto-locks after failed attempts  
✅ **OTP Expiry**: 10-minute OTP validity
✅ **JWT Tokens**: Secure session management
✅ **Password Strength**: Configurable requirements

---

## 🛡️ Production Ready

- **Database**: SQLite (dev) → PostgreSQL (production)
- **CORS**: Configurable for your domain
- **Logging**: Comprehensive security logging
- **Error Handling**: No information disclosure
- **Scalable**: Stateless JWT architecture

---

## 📱 E-commerce Integration

Perfect for:
- **User Registration**: Customer account creation
- **User Login**: Secure customer authentication  
- **Password Reset**: OTP-based password recovery
- **Profile Management**: User information updates
- **Session Management**: Secure login sessions

---

## 🚀 Quick Start

1. **Register User**: `POST /register`
2. **Login**: `POST /login` → Get JWT token
3. **Access Protected Routes**: Use `Authorization: Bearer <token>`
4. **Password Reset**: `POST /send-reset-otp` → `POST /reset-password-otp`

**That's it!** Your e-commerce authentication is ready.