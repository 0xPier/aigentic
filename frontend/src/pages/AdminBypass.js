import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Box, Typography, CircularProgress, Button } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

function AdminBypass() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [error, setError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(true);

  const handleAdminLogin = async () => {
    setIsLoggingIn(true);
    setError('');
    
    try {
      // Use the standard login endpoint with dev credentials
      const response = await api.post('/auth/login-json', {
        username: 'admin',
        password: 'admin123'
      });

      if (response.data && response.data.access_token) {
        // Store tokens in localStorage
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('refresh_token', response.data.refresh_token);
        
        // Force a page reload to properly initialize the auth context
        window.location.href = location.state?.from?.pathname || '/dashboard';
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (err) {
      console.error('Admin login error:', err);
      setError('Failed to log in as admin. Please make sure the backend is running in development mode.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  // Auto-trigger login on component mount
  useEffect(() => {
    if (user) {
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
      return;
    }
    
    handleAdminLogin();
  }, [user]);

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      textAlign="center"
      p={3}
    >
      {isLoggingIn ? (
        <>
          <CircularProgress size={60} thickness={4} sx={{ mb: 3 }} />
          <Typography variant="h5" gutterBottom>
            Development Admin Access
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Logging in as admin...
          </Typography>
        </>
      ) : error ? (
        <>
          <Typography variant="h5" gutterBottom color="error">
            Login Failed
          </Typography>
          <Typography color="error" sx={{ mb: 3 }}>{error}</Typography>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleAdminLogin}
            disabled={isLoggingIn}
            sx={{ mt: 2 }}
          >
            {isLoggingIn ? 'Logging in...' : 'Retry Admin Login'}
          </Button>
        </>
      ) : (
        <Typography variant="h5" gutterBottom color="success.main">
          Login Successful! Redirecting...
        </Typography>
      )}
      
      <Typography variant="caption" color="textSecondary" sx={{ mt: 4, display: 'block' }}>
        Note: This is a development-only feature and should be removed in production.
      </Typography>
    </Box>
  );
}

export default AdminBypass;
