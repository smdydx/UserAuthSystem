
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Auth API calls
export const authAPI = {
  register: (userData) => api.post('/auth/register', userData),
  login: (credentials) => api.post('/auth/login', credentials),
  logout: (refresh_token) => api.post('/auth/logout', { refresh_token }),
  refreshToken: (refresh_token) => api.post('/auth/refresh', { refresh_token }),
  getProfile: () => api.get('/auth/me'),
  
  // OTP Password Reset
  sendResetOTP: (email, method = 'email') => 
    api.post('/auth/send-reset-otp', { email, method }),
  resetPasswordWithOTP: (email, otp_code, new_password) =>
    api.post('/auth/reset-password-otp', { email, otp_code, new_password }),
  
  healthCheck: () => api.get('/auth/health'),
};

// Users API calls
export const usersAPI = {
  getUsers: (params = {}) => api.get('/users/', { params }),
  getUserById: (userId) => api.get(`/users/${userId}`),
  updateUser: (userId, userData) => api.put(`/users/${userId}`, userData),
  changePassword: (userId, passwordData) => 
    api.post(`/users/${userId}/change-password`, passwordData),
  deactivateUser: (userId) => api.post(`/users/${userId}/deactivate`),
  activateUser: (userId) => api.post(`/users/${userId}/activate`),
  deleteUser: (userId) => api.delete(`/users/${userId}`),
  getUserStatistics: () => api.get('/users/statistics'),
  getProfile: () => api.get('/users/profile'),
  
  // Role-specific endpoints
  getAdmins: () => api.get('/users/admins/'),
  getVendors: () => api.get('/users/vendors/'),
  getCustomers: () => api.get('/users/customers/'),
};

export default api;
