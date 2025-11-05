import axios from 'axios';
import { toast } from 'react-toastify';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://web-production-2fb7.up.railway.app';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }

    // Show error toast
    const errorMessage = error.response?.data?.message || 'An error occurred';
    toast.error(errorMessage);

    return Promise.reject(error);
  }
);

// API endpoints
export const apiEndpoints = {
  // Health and Info
  health: () => api.get('/'),
  info: () => api.get('/api/info'),

  // Authentication
  auth: {
    signup: (userData) => api.post('/api/auth/signup', userData),
    login: (credentials) => api.post('/api/auth/login', credentials),
    validate: (token) => api.get('/api/auth/validate', {
      headers: { Authorization: `Bearer ${token}` }
    }),
    updateProfile: (updateData) => api.put('/api/auth/profile', updateData),
    changePassword: (passwordData) => api.post('/api/auth/change-password', passwordData),
    forgotPassword: (email) => api.post('/api/auth/forgot-password', { email }),
    googleLogin: (tokenId) => api.post('/api/auth/google', { tokenId })
  },

  // Predictions
  predict: (patientData) => api.post('/api/predict', patientData),
  getHistory: () => api.get('/api/history'),
  getStatistics: () => api.get('/api/statistics'),
  deletePrediction: (predictionId) => api.delete(`/api/predictions/${predictionId}`)
};

// Helper functions
export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};

export const clearAuthToken = () => {
  delete api.defaults.headers.common['Authorization'];
};

export default api;
