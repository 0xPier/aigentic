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
  const [notifications, setNotifications] = useState(true);
  const [emailUpdates, setEmailUpdates] = useState(false);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <ProfileSettings />
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Preferences
              </Typography>
              <List>
                <ListItem>
                  <ListItemText
                    primary="Push Notifications"
                    secondary="Receive notifications for task completions and updates"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={notifications}
                      onChange={(e) => setNotifications(e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Email Updates"
                    secondary="Receive weekly summary emails"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={emailUpdates}
                      onChange={(e) => setEmailUpdates(e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <IntegrationsSettings />
        </Grid>
      </Grid>
    </Box>
  );
}

export default Settings;
