import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Divider,
  Alert,
  Card,
  CardContent,
  CardActions,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Container,
  CircularProgress,
} from '@mui/material';
import {
  Save as SaveIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';

import { useAuth } from '../../contexts/AuthContext';
import { usersAPI, fetchIntegrations, integrationsAPI } from '../../services/api';
import { adminAPI } from '../../services/api';

function ProfileSettings() {
  const { user } = useAuth();
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      full_name: user?.full_name || '',
      email: user?.email || '',
      username: user?.username || '',
    },
  });

  const updateProfileMutation = useMutation(usersAPI.updateProfile, {
    onSuccess: () => {
      setSuccess('Profile updated successfully');
      setError('');
    },
    onError: (error) => {
      setError(error.response?.data?.detail || 'Failed to update profile');
      setSuccess('');
    },
  });

  const onSubmit = (data) => {
    updateProfileMutation.mutate(data);
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Profile Settings
        </Typography>
        
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <form onSubmit={handleSubmit(onSubmit)}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Controller
                name="full_name"
                control={control}
                rules={{ required: 'Full name is required' }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Full Name"
                    fullWidth
                    error={!!errors.full_name}
                    helperText={errors.full_name?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="username"
                control={control}
                rules={{ required: 'Username is required' }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Username"
                    fullWidth
                    disabled
                    error={!!errors.username}
                    helperText={errors.username?.message || 'Username cannot be changed'}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <Controller
                name="email"
                control={control}
                rules={{ 
                  required: 'Email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address',
                  },
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Email"
                    fullWidth
                    error={!!errors.email}
                    helperText={errors.email?.message}
                  />
                )}
              />
            </Grid>
          </Grid>
        </form>
      </CardContent>
      <CardActions>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSubmit(onSubmit)}
          disabled={updateProfileMutation.isLoading}
        >
          Save Changes
        </Button>
      </CardActions>
    </Card>
  );
}

function IntegrationDialog({ open, onClose, integration, onSubmit, mode = 'create' }) {
  const [showApiKey, setShowApiKey] = useState(false);

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    defaultValues: {
      name: integration?.name || '',
      api_key: integration?.api_key || '',
      config: integration?.config || {},
    },
  });

  React.useEffect(() => {
    if (integration && mode === 'edit') {
      reset({
        name: integration.name,
        api_key: integration.api_key,
        config: integration.config,
      });
    }
  }, [integration, mode, reset]);

  const handleFormSubmit = (data) => {
    onSubmit(data);
    onClose();
  };

  const integrationTypes = [
    'openai',
    'twitter',
    'telegram',
    'stripe',
    'email',
    'crm',
    'image_generation',
  ];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {mode === 'create' ? 'Add Integration' : 'Edit Integration'}
      </DialogTitle>
      <form onSubmit={handleSubmit(handleFormSubmit)}>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2}>
            <Controller
              name="name"
              control={control}
              rules={{ required: 'Integration name is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Integration Type"
                  fullWidth
                  error={!!errors.name}
                  helperText={errors.name?.message}
                >
                  {integrationTypes.map((type) => (
                    <option key={type} value={type}>
                      {type.replace('_', ' ').toUpperCase()}
                    </option>
                  ))}
                </TextField>
              )}
            />
            
            <Controller
              name="api_key"
              control={control}
              rules={{ required: 'API key is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="API Key"
                  type={showApiKey ? 'text' : 'password'}
                  fullWidth
                  error={!!errors.api_key}
                  helperText={errors.api_key?.message}
                  InputProps={{
                    endAdornment: (
                      <IconButton
                        onClick={() => setShowApiKey(!showApiKey)}
                        edge="end"
                      >
                        {showApiKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    ),
                  }}
                />
              )}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained">
            {mode === 'create' ? 'Add' : 'Update'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

function IntegrationsSettings() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState(null);
  const [dialogMode, setDialogMode] = useState('create');
  const [error, setError] = useState('');

  const queryClient = useQueryClient();

  const {
    data: integrations,
    isLoading,
    error: fetchError,
  } = useQuery('integrations', fetchIntegrations);

  const createIntegrationMutation = useMutation(integrationsAPI.createIntegration, {
    onSuccess: () => {
      queryClient.invalidateQueries('integrations');
      setError('');
    },
    onError: (error) => {
      setError(error.response?.data?.detail || 'Failed to create integration');
    },
  });

  const updateIntegrationMutation = useMutation(
    ({ integrationId, data }) => integrationsAPI.updateIntegration(integrationId, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('integrations');
        setError('');
      },
      onError: (error) => {
        setError(error.response?.data?.detail || 'Failed to update integration');
      },
    }
  );

  const deleteIntegrationMutation = useMutation(integrationsAPI.deleteIntegration, {
    onSuccess: () => {
      queryClient.invalidateQueries('integrations');
      setError('');
    },
    onError: (error) => {
      setError(error.response?.data?.detail || 'Failed to delete integration');
    },
  });

  const handleAddIntegration = () => {
    setSelectedIntegration(null);
    setDialogMode('create');
    setDialogOpen(true);
  };

  const handleEditIntegration = (integration) => {
    setSelectedIntegration(integration);
    setDialogMode('edit');
    setDialogOpen(true);
  };

  const handleDeleteIntegration = (integrationId) => {
    if (window.confirm('Are you sure you want to delete this integration?')) {
      deleteIntegrationMutation.mutate(integrationId);
    }
  };

  const handleIntegrationSubmit = (data) => {
    if (dialogMode === 'create') {
      createIntegrationMutation.mutate(data);
    } else {
      updateIntegrationMutation.mutate({ 
        integrationId: selectedIntegration.id, 
        data 
      });
    }
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            API Integrations
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddIntegration}
          >
            Add Integration
          </Button>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {fetchError && <Alert severity="error" sx={{ mb: 2 }}>Failed to load integrations</Alert>}

        <List>
          {integrations?.map((integration) => (
            <ListItem key={integration.id} divider>
              <ListItemText
                primary={integration.name.replace('_', ' ').toUpperCase()}
                secondary={`Added: ${new Date(integration.created_at).toLocaleDateString()}`}
              />
              <Box display="flex" alignItems="center" gap={1}>
                <Chip
                  label={integration.is_active ? 'Active' : 'Inactive'}
                  color={integration.is_active ? 'success' : 'default'}
                  size="small"
                />
                <IconButton
                  size="small"
                  onClick={() => handleEditIntegration(integration)}
                >
                  <EditIcon />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={() => handleDeleteIntegration(integration.id)}
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            </ListItem>
          )) || (
            <ListItem>
              <ListItemText
                primary="No integrations configured"
                secondary="Add your first API integration to enable advanced features"
              />
            </ListItem>
          )}
        </List>
      </CardContent>

      <IntegrationDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        integration={selectedIntegration}
        onSubmit={handleIntegrationSubmit}
        mode={dialogMode}
      />
    </Card>
  );
}

function Settings() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm();

  const isAdmin = user?.role === 'admin';

  const onCreateUser = async (data) => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await adminAPI.createUser(data);
      setSuccess(`User ${data.username} created successfully!`);
      reset();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>

        {/* User Info */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            User Information
          </Typography>
          <Typography><strong>Username:</strong> {user?.username}</Typography>
          <Typography><strong>Email:</strong> {user?.email}</Typography>
          <Typography><strong>Full Name:</strong> {user?.full_name}</Typography>
          <Typography><strong>Role:</strong> {user?.role}</Typography>
          <Typography><strong>Subscription:</strong> {user?.subscription_tier}</Typography>
        </Paper>

        {/* Admin Functions */}
        {isAdmin && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Admin Functions
            </Typography>
            <Divider sx={{ mb: 3 }} />

            <Typography variant="subtitle1" gutterBottom>
              Create New User
            </Typography>

            {success && (
              <Alert severity="success" sx={{ mb: 2 }}>
                {success}
              </Alert>
            )}

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <Box
              component="form"
              onSubmit={handleSubmit(onCreateUser)}
              sx={{ mt: 2 }}
            >
              <TextField
                margin="normal"
                required
                fullWidth
                label="Username"
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
                label="Email"
                type="email"
                error={!!errors.email}
                helperText={errors.email?.message}
                {...register('email', {
                  required: 'Email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address',
                  },
                })}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                label="Full Name"
                error={!!errors.full_name}
                helperText={errors.full_name?.message}
                {...register('full_name', {
                  required: 'Full name is required',
                })}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                label="Password"
                type="password"
                error={!!errors.password}
                helperText={errors.password?.message}
                {...register('password', {
                  required: 'Password is required',
                  minLength: {
                    value: 8,
                    message: 'Password must be at least 8 characters',
                  },
                })}
              />
              <Button
                type="submit"
                variant="contained"
                sx={{ mt: 2 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Create User'}
              </Button>
            </Box>
          </Paper>
        )}
      </Box>
    </Container>
  );
}

export default Settings;
