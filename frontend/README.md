# E-commerce Frontend

## Overview

यह एक complete frontend application है जो आपके FastAPI backend के साथ connect होता है। यह अलग port (3000) पर चलता है और सभी authentication APIs को handle करता है।

## Features

### 🔐 Authentication System
- **User Registration**: नया account बनाने के लिए
- **Login/Logout**: Secure JWT token-based authentication
- **Password Reset**: OTP-based password reset
- **Email Verification**: Account verification system

### 🎨 UI Features
- **Modern Design**: Clean और responsive interface
- **Loading States**: सभी API calls के लिए loading indicators
- **Error Handling**: User-friendly error messages
- **Form Validation**: Frontend form validation
- **Auto Token Refresh**: Automatic access token refresh

### 📱 Dashboard
- **User Profile**: Complete user information display
- **API Testing**: Protected endpoints को test करने के लिए
- **Token Management**: Automatic token handling

## How to Run

### Backend (Port 5000)
```bash
# Already running
python main.py
```

### Frontend (Port 8080)
```bash
cd frontend
node server.js
```

## File Structure

```
frontend/
├── index.html          # Main HTML file with all forms
├── api.js             # API client with all backend connections
├── app.js             # Frontend logic and event handlers
├── package.json       # Project configuration
└── README.md          # This file
```

## API Endpoints Connected

### Authentication APIs
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/send-reset-otp` - Send password reset OTP
- `POST /api/v1/auth/reset-password-otp` - Reset password with OTP
- `POST /api/v1/auth/verify-email` - Email verification

### User APIs
- `GET /api/v1/users/me` - Get current user profile

## Features in Detail

### 1. Registration Flow
1. User fills registration form
2. API call to `/auth/register`
3. Success message + email verification sent
4. Redirect to login page

### 2. Login Flow
1. User enters credentials
2. API call to `/auth/login`
3. Store access + refresh tokens
4. Redirect to dashboard

### 3. Auto Token Refresh
- Automatic detection of expired tokens
- Auto refresh using refresh token
- Seamless user experience

### 4. Password Reset Flow
1. User enters email
2. API call to `/auth/send-reset-otp`
3. OTP form appears
4. User enters OTP + new password
5. API call to `/auth/reset-password-otp`
6. Success → redirect to login

### 5. Dashboard Features
- User profile display
- Protected API testing
- Logout functionality

## Configuration

### API Base URL
```javascript
const API_BASE_URL = 'http://localhost:5000/api/v1';
```

### Token Storage
- Access tokens stored in localStorage
- Refresh tokens stored in localStorage
- Automatic cleanup on logout

## Security Features

### Token Management
- Automatic token refresh
- Secure token storage
- Token expiration handling

### Form Validation
- Client-side validation
- Server-side error handling
- User-friendly error messages

### CORS Handling
- Backend configured for frontend port
- Proper headers for API calls

## Usage Instructions

### For Development
1. Start backend on port 5000
2. Start frontend on port 8080
3. Open browser at `http://localhost:8080`

### For Testing
- Use the dashboard API test feature
- Check browser console for detailed logs
- Monitor network tab for API calls

## Browser Support
- Chrome (recommended)
- Firefox
- Safari
- Edge

## Next Steps
- Add email verification UI
- Add profile update functionality
- Add product catalog integration
- Add shopping cart features