# Login में 2 Tokens क्यों? - Practical Example

## 🤔 आपका सवाल: "Refresh automatic hai to login में 2 tokens kyun?"

**जवाब**: Login में **refresh token** देना जरूरी है क्योंकि frontend को पता होना चाहिए कि **कैसे refresh करना है**!

---

## 🔄 Real Flow समझते हैं:

### **Step 1: User Login**
```javascript
// User logs in
POST /api/v1/auth/login
{
  "email": "user@example.com", 
  "password": "password123"
}

// Server Response - 2 tokens दिए जाते हैं
{
  "access_token": "abc123...",     // 30 मिनट के लिए
  "refresh_token": "xyz789...",    // 7 दिन के लिए
  "expires_in": 1800
}
```

### **Step 2: Frontend stores both tokens**
```javascript
// Frontend दोनों tokens store करता है
localStorage.setItem('access_token', response.access_token);
localStorage.setItem('refresh_token', response.refresh_token);
```

### **Step 3: API calls (30 मिनट तक)**
```javascript
// हर API call में access token use होता है
fetch('/api/v1/products', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

### **Step 4: Access token expires (30 मिनट बाद)**
```javascript
// API call fails - 401 Unauthorized
fetch('/api/v1/products') // ❌ Fails

// Frontend automatically refreshes
fetch('/api/v1/auth/refresh', {
  method: 'POST',
  body: JSON.stringify({
    refresh_token: localStorage.getItem('refresh_token')  // यहाँ use होता है!
  })
});

// New access token मिलता है
{
  "access_token": "new_abc123...",
  "expires_in": 1800
}
```

---

## 💡 अब समझ आया?

### **अगर login में सिर्फ 1 token दिया जाए:**
```javascript
// Login response
{
  "access_token": "abc123...",
  // ❌ No refresh token
}

// 30 मिनट बाद
fetch('/api/v1/products') // ❌ Fails
// Frontend: "अब कैसे refresh करूं? Token नहीं है!"
// Result: User को फिर से login करना पड़ेगा!
```

### **हमारा 2-token system:**
```javascript
// Login response
{
  "access_token": "abc123...",
  "refresh_token": "xyz789..."  // ✅ Refresh के लिए
}

// 30 मिनट बाद
fetch('/api/v1/products') // ❌ Fails
// Frontend: "No problem! Refresh token use करके नया token लेता हूं"
fetch('/api/v1/auth/refresh', {
  body: JSON.stringify({
    refresh_token: "xyz789..."  // ✅ यहाँ use होता है!
  })
});
// Result: User को login नहीं करना पड़ा!
```

---

## 🎯 Simple Summary:

**Q: Login में refresh token क्यों?**  
**A: ताकि frontend को पता हो कि नया access token कैसे लेना है!**

**Q: Refresh automatic क्यों नहीं?**  
**A: Server को पता नहीं कि कौन सा user refresh करना चाहता है। Frontend को refresh token भेजना पड़ता है।**

---

## 🏪 E-commerce Example:

```javascript
// Customer shops on website
1. Login → Get access + refresh token
2. Add to cart (access token works)
3. Browse products (access token works)
4. 30 minutes later...
5. Checkout → Access token expired!
6. Frontend: "Let me refresh automatically"
7. POST /refresh with refresh_token
8. Get new access token
9. Checkout successful!
10. Customer happy - no re-login needed!
```

**Bottom line**: Login में refresh token इसलिए दिया जाता है ताकि user को 30 मिनट बाद फिर से login न करना पड़े!