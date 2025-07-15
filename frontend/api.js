// API Configuration
const API_BASE_URL = 'http://localhost:5000/api/v1';

// API Client Class
class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
    }

    // Get authorization headers
    getAuthHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.accessToken}`
        };
    }

    // Set tokens in localStorage
    setTokens(accessToken, refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    }

    // Clear tokens
    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }

    // Refresh access token
    async refreshAccessToken() {
        try {
            const response = await fetch(`${this.baseURL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh_token: this.refreshToken
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.setTokens(data.access_token, this.refreshToken);
                return true;
            } else {
                this.clearTokens();
                return false;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
            this.clearTokens();
            return false;
        }
    }

    // Make API request with automatic token refresh
    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        // First attempt
        let response = await fetch(url, options);
        
        // If unauthorized and we have a refresh token, try to refresh
        if (response.status === 401 && this.refreshToken) {
            const refreshed = await this.refreshAccessToken();
            if (refreshed) {
                // Update headers with new token
                options.headers = {
                    ...options.headers,
                    'Authorization': `Bearer ${this.accessToken}`
                };
                // Retry the request
                response = await fetch(url, options);
            }
        }
        
        return response;
    }

    // Register user
    async register(userData) {
        try {
            const response = await fetch(`${this.baseURL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();
            
            if (response.ok) {
                return { success: true, data };
            } else {
                return { success: false, error: data.error || 'Registration failed' };
            }
        } catch (error) {
            return { success: false, error: 'Network error occurred' };
        }
    }

    // Login user
    async login(credentials) {
        try {
            const response = await fetch(`${this.baseURL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(credentials)
            });

            const data = await response.json();
            
            if (response.ok) {
                this.setTokens(data.access_token, data.refresh_token);
                return { success: true, data };
            } else {
                return { success: false, error: data.error || 'Login failed' };
            }
        } catch (error) {
            return { success: false, error: 'Network error occurred' };
        }
    }

    // Get current user
    async getCurrentUser() {
        try {
            const response = await this.makeRequest('/users/me', {
                method: 'GET',
                headers: this.getAuthHeaders()
            });

            if (response.ok) {
                const data = await response.json();
                return { success: true, data };
            } else {
                const error = await response.json();
                return { success: false, error: error.error || 'Failed to get user' };
            }
        } catch (error) {
            return { success: false, error: 'Network error occurred' };
        }
    }

    // Send password reset OTP
    async sendResetOTP(email) {
        try {
            const response = await fetch(`${this.baseURL}/auth/send-reset-otp`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email })
            });

            const data = await response.json();
            
            if (response.ok) {
                return { success: true, data };
            } else {
                return { success: false, error: data.error || 'Failed to send OTP' };
            }
        } catch (error) {
            return { success: false, error: 'Network error occurred' };
        }
    }

    // Reset password with OTP
    async resetPasswordWithOTP(resetData) {
        try {
            const response = await fetch(`${this.baseURL}/auth/reset-password-otp`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(resetData)
            });

            const data = await response.json();
            
            if (response.ok) {
                return { success: true, data };
            } else {
                return { success: false, error: data.error || 'Password reset failed' };
            }
        } catch (error) {
            return { success: false, error: 'Network error occurred' };
        }
    }

    // Verify email
    async verifyEmail(token) {
        try {
            const response = await fetch(`${this.baseURL}/auth/verify-email`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token })
            });

            const data = await response.json();
            
            if (response.ok) {
                return { success: true, data };
            } else {
                return { success: false, error: data.error || 'Email verification failed' };
            }
        } catch (error) {
            return { success: false, error: 'Network error occurred' };
        }
    }

    // Logout
    async logout() {
        try {
            const response = await this.makeRequest('/auth/logout', {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            this.clearTokens();
            return response.ok;
        } catch (error) {
            this.clearTokens();
            return false;
        }
    }

    // Test protected endpoint
    async testProtectedEndpoint() {
        try {
            const response = await this.makeRequest('/users/me', {
                method: 'GET',
                headers: this.getAuthHeaders()
            });

            if (response.ok) {
                const data = await response.json();
                return { success: true, data };
            } else {
                const error = await response.json();
                return { success: false, error: error.error || 'Test failed' };
            }
        } catch (error) {
            return { success: false, error: 'Network error occurred' };
        }
    }
}

// Initialize API client
const api = new APIClient(API_BASE_URL);