# JWT Token System Explanation - दो Tokens क्यों?

## 🔑 दो Token System का फायदा

### 1. **Access Token** (छोटी अवधि - 30 मिनट)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800  // 30 minutes
}
```
- **काम**: हर API call के लिए इस्तेमाल होता है
- **समय**: 30 मिनट की अवधि  
- **सुरक्षा**: जल्दी expire हो जाता है

### 2. **Refresh Token** (लंबी अवधि - 7 दिन)
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 604800  // 7 days
}
```
- **काम**: नया access token बनाने के लिए
- **समय**: 7 दिन की अवधि
- **सुरक्षा**: Database में store होता है

---

## 💡 Security Benefits

### अगर Access Token चोरी हो जाए:
- ✅ **30 मिनट बाद automatically expire** हो जाएगा
- ✅ **कम नुकसान** क्योंकि छोटी अवधि
- ✅ **Database में revoke** कर सकते हैं

### अगर Refresh Token चोरी हो जाए:
- ✅ **Database से तुरंत revoke** कर सकते हैं
- ✅ **सभी devices से logout** कर सकते हैं
- ✅ **New tokens नहीं बन सकते**

---

## 🔄 How it Works in E-commerce

### User Login Process:
1. **User enters email/password**
2. **Server validates credentials**
3. **Server returns 2 tokens**:
   - Access Token (30 min)
   - Refresh Token (7 days)

### Frontend Usage:
```javascript
// Store tokens
localStorage.setItem('access_token', response.access_token);
localStorage.setItem('refresh_token', response.refresh_token);

// Use access token for API calls
fetch('/api/v1/products', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

### Auto Token Refresh:
```javascript
// When access token expires (30 min)
fetch('/api/v1/auth/refresh', {
  method: 'POST',
  body: JSON.stringify({
    refresh_token: localStorage.getItem('refresh_token')
  })
});
```

---

## 📱 E-commerce Use Cases

### Customer Shopping Experience:
1. **Login once** → Get 2 tokens
2. **Shop for 30 minutes** → Access token works
3. **After 30 minutes** → Auto refresh with refresh token
4. **Continue shopping** → Seamless experience for 7 days
5. **Logout** → Both tokens revoked

### Admin Panel:
1. **Admin login** → Get 2 tokens
2. **Manage products** → Access token for API calls
3. **Long session** → Auto refresh every 30 minutes
4. **Security** → Can revoke all sessions if needed

---

## 🛡️ Security Advantages

### Traditional Single Token:
❌ **Long expiry** = Security risk  
❌ **Short expiry** = User frustration  
❌ **Hard to revoke** = Security issue

### Our 2-Token System:
✅ **Best security** = Short-lived access tokens  
✅ **Best UX** = Auto refresh for 7 days  
✅ **Easy revocation** = Database-controlled refresh tokens

---

## 🎯 Simple Summary

**Access Token** = रोजाना का काम (30 मिनट)  
**Refresh Token** = नया access token लेने के लिए (7 दिन)

**फायदा**: User को बार-बार login नहीं करना पड़ता, लेकिन security भी tight रहती है!

---

## 🔧 Configuration in Your Project

```python
# app/core/config.py
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30    # Access token
REFRESH_TOKEN_EXPIRE_DAYS: int = 7       # Refresh token
```

यह industry standard है और सभी बड़े platforms (Google, Facebook, Amazon) इसी system का इस्तेमाल करते हैं।