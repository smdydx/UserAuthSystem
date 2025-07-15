// DOM Elements
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const forgotPasswordForm = document.getElementById('forgotPasswordForm');
const otpForm = document.getElementById('otpForm');
const dashboard = document.getElementById('dashboard');

// Form Elements
const loginFormElement = document.getElementById('loginFormElement');
const registerFormElement = document.getElementById('registerFormElement');
const forgotPasswordFormElement = document.getElementById('forgotPasswordFormElement');
const otpFormElement = document.getElementById('otpFormElement');

// Message Elements
const message = document.getElementById('message');
const registerMessage = document.getElementById('registerMessage');
const forgotMessage = document.getElementById('forgotMessage');
const otpMessage = document.getElementById('otpMessage');

// Toggle Links
const showRegister = document.getElementById('showRegister');
const showLogin = document.getElementById('showLogin');
const showForgotPassword = document.getElementById('showForgotPassword');
const backToLogin = document.getElementById('backToLogin');
const backToForgot = document.getElementById('backToForgot');

// Buttons
const loginBtn = document.getElementById('loginBtn');
const registerBtn = document.getElementById('registerBtn');
const forgotBtn = document.getElementById('forgotBtn');
const otpBtn = document.getElementById('otpBtn');
const logoutBtn = document.getElementById('logoutBtn');
const testApiBtn = document.getElementById('testApiBtn');

// Loading indicators
const loginLoading = document.getElementById('loginLoading');
const registerLoading = document.getElementById('registerLoading');
const forgotLoading = document.getElementById('forgotLoading');
const otpLoading = document.getElementById('otpLoading');

// User data storage
let currentUserEmail = '';

// Utility Functions
function showMessage(element, text, type = 'error') {
    element.innerHTML = `<div class="message ${type}">${text}</div>`;
    setTimeout(() => {
        element.innerHTML = '';
    }, 5000);
}

function showLoading(button, loadingElement, textElement) {
    button.disabled = true;
    loadingElement.classList.remove('hidden');
    textElement.classList.add('hidden');
}

function hideLoading(button, loadingElement, textElement) {
    button.disabled = false;
    loadingElement.classList.add('hidden');
    textElement.classList.remove('hidden');
}

function showForm(formToShow) {
    // Hide all forms
    loginForm.classList.add('hidden');
    registerForm.classList.add('hidden');
    forgotPasswordForm.classList.add('hidden');
    otpForm.classList.add('hidden');
    dashboard.classList.add('hidden');
    
    // Show selected form
    formToShow.classList.remove('hidden');
    
    // Clear all messages
    message.innerHTML = '';
    registerMessage.innerHTML = '';
    forgotMessage.innerHTML = '';
    otpMessage.innerHTML = '';
}

// Check if user is logged in
function checkAuth() {
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) {
        loadDashboard();
    } else {
        showForm(loginForm);
    }
}

// Load dashboard
async function loadDashboard() {
    const result = await api.getCurrentUser();
    
    if (result.success) {
        // Show dashboard
        showForm(dashboard);
        
        // Fill user data
        document.getElementById('userName').textContent = result.data.full_name || 'N/A';
        document.getElementById('userEmail').textContent = result.data.email;
        document.getElementById('userRole').textContent = result.data.role;
        document.getElementById('userStatus').textContent = result.data.is_verified ? 'Verified' : 'Not Verified';
    } else {
        // Token expired or invalid
        api.clearTokens(); // Clear invalid tokens
        showForm(loginForm);
    }
}

// Event Listeners

// Form toggles
showRegister.addEventListener('click', (e) => {
    e.preventDefault();
    showForm(registerForm);
});

showLogin.addEventListener('click', (e) => {
    e.preventDefault();
    showForm(loginForm);
});

showForgotPassword.addEventListener('click', (e) => {
    e.preventDefault();
    showForm(forgotPasswordForm);
});

backToLogin.addEventListener('click', (e) => {
    e.preventDefault();
    showForm(loginForm);
});

backToForgot.addEventListener('click', (e) => {
    e.preventDefault();
    showForm(forgotPasswordForm);
});

// Login Form
loginFormElement.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    showLoading(loginBtn, loginLoading, document.getElementById('loginBtnText'));
    
    const result = await api.login({ email, password });
    
    hideLoading(loginBtn, loginLoading, document.getElementById('loginBtnText'));
    
    if (result.success) {
        showMessage(message, 'Login successful!', 'success');
        setTimeout(() => {
            loadDashboard();
        }, 1000);
    } else {
        showMessage(message, result.error);
    }
});

// Register Form
registerFormElement.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const full_name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    showLoading(registerBtn, registerLoading, document.getElementById('registerBtnText'));
    
    const result = await api.register({ full_name, email, password });
    
    hideLoading(registerBtn, registerLoading, document.getElementById('registerBtnText'));
    
    if (result.success) {
        showMessage(registerMessage, 'Registration successful! Please check your email for verification.', 'success');
        setTimeout(() => {
            showForm(loginForm);
        }, 2000);
    } else {
        showMessage(registerMessage, result.error);
    }
});

// Forgot Password Form
forgotPasswordFormElement.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('forgotEmail').value;
    currentUserEmail = email;
    
    showLoading(forgotBtn, forgotLoading, document.getElementById('forgotBtnText'));
    
    const result = await api.sendResetOTP(email);
    
    hideLoading(forgotBtn, forgotLoading, document.getElementById('forgotBtnText'));
    
    if (result.success) {
        showMessage(forgotMessage, 'OTP sent successfully! Check your email.', 'success');
        setTimeout(() => {
            showForm(otpForm);
        }, 1000);
    } else {
        showMessage(forgotMessage, result.error);
    }
});

// OTP Form
otpFormElement.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const otp_code = document.getElementById('otpCode').value;
    const new_password = document.getElementById('newPassword').value;
    
    showLoading(otpBtn, otpLoading, document.getElementById('otpBtnText'));
    
    const result = await api.resetPasswordWithOTP({
        email: currentUserEmail,
        otp_code,
        new_password
    });
    
    hideLoading(otpBtn, otpLoading, document.getElementById('otpBtnText'));
    
    if (result.success) {
        showMessage(otpMessage, 'Password reset successful! You can now login.', 'success');
        setTimeout(() => {
            showForm(loginForm);
        }, 2000);
    } else {
        showMessage(otpMessage, result.error);
    }
});

// Logout
logoutBtn.addEventListener('click', async () => {
    await api.logout();
    showForm(loginForm);
});

// Test API
testApiBtn.addEventListener('click', async () => {
    const result = await api.testProtectedEndpoint();
    const responseDiv = document.getElementById('apiResponse');
    
    if (result.success) {
        responseDiv.innerHTML = `<strong>Success:</strong><br>${JSON.stringify(result.data, null, 2)}`;
    } else {
        responseDiv.innerHTML = `<strong>Error:</strong><br>${result.error}`;
    }
});

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});