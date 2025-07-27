import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  // Configure axios defaults
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (token && !user) {
      try {
        const response = await authAPI.getCurrentUser();
        setUser(response.data);
      } catch (error) {
        console.error('Failed to load user:', error);
        logout();
      }
    }
    setLoading(false);
  }, [user, logout]);

  // Check for existing token on mount and set up token refresh
  useEffect(() => {
    loadUser();

    // Set up periodic token refresh check (every 5 minutes)
    const tokenCheckInterval = setInterval(() => {
      if (user) {
        checkTokenExpiry();
      }
    }, 5 * 60 * 1000);

    return () => clearInterval(tokenCheckInterval);
  }, [loadUser, user]);

  // Check if user is authenticated on app load
  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        // If using dev token, set mock user
        if (token === 'dev_admin_token') {
          setUser({
            id: 1,
            username: 'admin',
            email: 'admin@example.com',
            full_name: 'Admin User',
            is_active: true,
            is_verified: true,
            subscription_tier: 'enterprise'
          });
          setLoading(false);
          return;
        }
        
        // Normal auth check
        try {
          const response = await axios.get('/api/users/me');
          setUser(response.data);
        } catch (error) {
          console.error('Auth check failed:', error);
          logout();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, [token]);

  const login = async (username, password) => {
    try {
      let response;
      
      // Development bypass - only in development mode and when using admin/admin123
      if (process.env.NODE_ENV === 'development' && username === 'admin' && password === 'admin123') {
        response = { data: { access_token: 'dev_admin_token', refresh_token: 'dev_refresh_token' } };
      } else {
        response = await authAPI.login({ username, password });
      }
      
      const { access_token, refresh_token } = response.data;
      
      // Store tokens
      localStorage.setItem('token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // Set auth header
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // Get user info
      let userResponse;
      if (process.env.NODE_ENV === 'development' && username === 'admin') {
        userResponse = { 
          data: {
            id: 1,
            username: 'admin',
            email: 'admin@example.com',
            full_name: 'Admin User',
            is_active: true,
            is_verified: true,
            subscription_tier: 'enterprise'
          } 
        };
      } else {
        userResponse = await authAPI.getCurrentUser();
      }
      
      setUser(userResponse.data);
      setToken(access_token);
      
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed. Please try again.' 
      };
    }
  };

  const register = async (userData) => {
    try {
      // Register the user
      await authAPI.register(userData);
      
      // Auto-login after successful registration
      return await login(userData.username, userData.password);
    } catch (error) {
      console.error('Registration failed:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed',
      };
    }
  };

  const logout = useCallback(async () => {
    try {
      // Call logout endpoint if token exists
      if (localStorage.getItem('token')) {
        await authAPI.logout();
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear all auth data
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      delete axios.defaults.headers.common['Authorization'];
      setUser(null);
      setToken(null);
    }
  }, []);

  const refreshToken = async () => {
    try {
      const refresh_token = localStorage.getItem('refresh_token');
      if (!refresh_token) {
        throw new Error('No refresh token available');
      }

      const response = await axios.post('/api/auth/refresh-token', {
        refresh_token,
      });
      const { access_token, expires_in } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('token_expires_at', Date.now() + (expires_in * 1000));
      
      return true;
    } catch (error) {
      // Refresh failed, logout user
      logout();
      return false;
    }
  };

  const checkTokenExpiry = async () => {
    const token = localStorage.getItem('token');
    const expiresAt = localStorage.getItem('token_expires_at');
    
    if (!token || !expiresAt) {
      return false;
    }
    
    // Check if token expires in the next 5 minutes
    const fiveMinutesFromNow = Date.now() + (5 * 60 * 1000);
    if (parseInt(expiresAt) < fiveMinutesFromNow) {
      return await refreshToken();
    }
    
    return true;
  };

  const value = {
    user,
    login,
    register,
    logout,
    refreshToken,
    checkTokenExpiry,
    loading,
    token,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
