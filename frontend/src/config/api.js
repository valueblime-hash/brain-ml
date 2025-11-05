// API Configuration for Brain Stroke Prediction Frontend
// This file handles the backend API URL configuration for different environments

const API_CONFIG = {
  // Base URL for the backend API
  BASE_URL: process.env.REACT_APP_API_URL || 'https://web-production-2fb7.up.railway.app',

  // API endpoints
  ENDPOINTS: {
    // Health and Info
    HEALTH: '/',
    API_INFO: '/api/info',

    // Authentication
    AUTH: {
      SIGNUP: '/api/auth/signup',
      LOGIN: '/api/auth/login',
      VALIDATE: '/api/auth/validate',
      PROFILE: '/api/auth/profile',
      CHANGE_PASSWORD: '/api/auth/change-password',
      FORGOT_PASSWORD: '/api/auth/forgot-password',
      GOOGLE: '/api/auth/google'
    },

    // Predictions
    PREDICT: '/api/predict',
    HISTORY: '/api/history',
    STATISTICS: '/api/statistics',
    DELETE_PREDICTION: (id) => `/api/predictions/${id}`
  },

  // Request timeout (30 seconds)
  TIMEOUT: 30000,

  // Default headers
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
};

// Helper function to get the full API URL
export const getApiUrl = (endpoint = '') => {
  const baseUrl = API_CONFIG.BASE_URL.replace(/\/$/, ''); // Remove trailing slash
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
};

// Helper function to get authorization headers
export const getAuthHeaders = (token = null) => {
  const headers = { ...API_CONFIG.DEFAULT_HEADERS };

  // Get token from localStorage if not provided
  const authToken = token || localStorage.getItem('token');

  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  return headers;
};

// Environment-specific configurations
export const ENV_CONFIG = {
  development: {
    API_URL: 'http://localhost:5000',
    DEBUG: true
  },
  production: {
    API_URL: 'https://web-production-52e4b.up.railway.app',
    DEBUG: false
  }
};

// Get current environment configuration
export const getCurrentEnvConfig = () => {
  const env = process.env.NODE_ENV || 'development';
  return ENV_CONFIG[env] || ENV_CONFIG.development;
};

// Axios default configuration
export const AXIOS_CONFIG = {
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: API_CONFIG.DEFAULT_HEADERS,
  withCredentials: false // Set to true if you need cookies/credentials
};

export default API_CONFIG;
