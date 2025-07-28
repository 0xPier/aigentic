import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import { useForm } from 'react-hook-form';

import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';

function Login() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();
  const [isDev, setIsDev] = useState(false);

  useEffect(() => {
    // Check if we're in development mode
    setIsDev(process.env.NODE_ENV === 'development');
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();

  const handleDevLogin = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/api/admin/dev-login');
      const { access_token, refresh_token, user } = response.data;
      
      // Store tokens
      localStorage.setItem('token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // Update auth context directly
      const result = await login('admin', 'admin123');
      if (result.success) {
        navigate('/dashboard');
      } else {
        setError('Development login failed');
      }
    } catch (err) {
      setError('Development login failed. Make sure the backend is running in development mode.');
      console.error('Dev login error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    setError('');

    try {
      // Use the standard login flow for demo user
      const result = await login('demo', 'demo123');
      
      if (result.success) {
        navigate('/dashboard');
      } else {
        setError(result.error || 'Demo login failed');
      }
    } catch (err) {
      setError('Demo login failed. Please try again.');
      console.error('Demo login error:', err);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data) => {
    setLoading(true);
    setError('');

    try {
      const result = await login(data.username, data.password);
      
      if (result.success) {
        navigate('/dashboard', { replace: true });
      } else {
        setError(result.error || 'Invalid username or password');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="sm">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ padding: 4, width: '100%' }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}
          >
            <Typography component="h1" variant="h4" gutterBottom>
              AI Consultancy Platform
            </Typography>
            <Typography variant="h5" color="textSecondary" gutterBottom>
              Sign In
            </Typography>

            {error && (
              <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
                {error}
              </Alert>
            )}

            <Box
              component="form"
              onSubmit={handleSubmit(onSubmit)}
              sx={{ mt: 1, width: '100%' }}
            >
              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="Username"
                name="username"
                autoComplete="username"
                autoFocus
                error={!!errors.username}
                helperText={errors.username?.message}
                {...register('username', {
                  required: 'Username is required',
                  minLength: {
                    value: 3,
                    message: 'Username must be at least 3 characters',
                  },
                })}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type="password"
                id="password"
                autoComplete="current-password"
                error={!!errors.password}
                helperText={errors.password?.message}
                {...register('password', {
                  required: 'Password is required',
                  minLength: {
                    value: 6,
                    message: 'Password must be at least 6 characters',
                  },
                })}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Sign In'}
              </Button>

              {/* Demo Login Button */}
              <Box sx={{ mt: 2 }}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={handleDemoLogin}
                  disabled={loading}
                  sx={{ mb: 1 }}
                >
                  {loading ? <CircularProgress size={24} /> : 'Demo Login'}
                </Button>
                <Typography variant="body2" color="text.secondary" align="center">
                  Username: demo, Password: demo123
                </Typography>
              </Box>

              {/* Development only - Admin bypass */}
              {isDev && (
                <Box sx={{ mt: 2 }}>
                  <Divider sx={{ my: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Development Only
                    </Typography>
                  </Divider>
                  <Button
                    fullWidth
                    variant="outlined"
                    color="warning"
                    onClick={handleDevLogin}
                    disabled={loading}
                  >
                    Admin Bypass Login
                  </Button>
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              <Box textAlign="center">
                <Typography variant="body2">
                  Don't have an account?{' '}
                  <Link to="/register" style={{ textDecoration: 'none' }}>
                    <Button variant="text" color="primary">
                      Sign Up
                    </Button>
                  </Link>
                </Typography>
              </Box>
            </Box>
          </Box>
        </Paper>

        {/* Demo Credentials */}
        <Paper elevation={1} sx={{ mt: 2, p: 2, width: '100%', bgcolor: 'grey.50' }}>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            Demo Credentials:
          </Typography>
          <Typography variant="body2" component="div">
            <strong>Username:</strong> demo
          </Typography>
          <Typography variant="body2" component="div">
            <strong>Password:</strong> demo123
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
}

export default Login;
