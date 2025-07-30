import { useState, useEffect } from 'react';
import { Box, Button, Typography, Paper, TextField, Select, MenuItem, FormControl, InputLabel, Switch, FormControlLabel, Alert, CircularProgress } from '@mui/material';
import { apiCall } from '../src/utils/api';

export default function Settings() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [testingIntegrations, setTestingIntegrations] = useState(false);
  const [integrationResults, setIntegrationResults] = useState(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setError(null);
      const data = await apiCall('/settings');
      setSettings(data);
    } catch (error) {
      setError('Failed to load settings: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      await apiCall('/settings', {
        method: 'PUT',
        body: JSON.stringify(settings),
      });
      setSuccessMessage('Settings saved successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error) {
      setError('Failed to save settings: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  const testIntegrations = async () => {
    setTestingIntegrations(true);
    setError(null);
    try {
      const results = await apiCall('/settings/test-integrations', {
        method: 'POST'
      });
      setIntegrationResults(results);
    } catch (error) {
      setError('Failed to test integrations: ' + error.message);
    } finally {
      setTestingIntegrations(false);
    }
  };

  const testLLMConnection = async () => {
    try {
      setError(null);
      const result = await apiCall('/settings/test-llm-connection', {
        method: 'POST'
      });
      setSuccessMessage('LLM connection successful!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error) {
      setError('LLM connection failed: ' + error.message);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings({ ...settings, [name]: type === 'checkbox' ? checked : value });
  };

  const renderIntegrationResults = () => {
    if (!integrationResults) return null;
    
    return (
      <Paper sx={{ p: 2, mt: 2 }}>
        <Typography variant="h6">Integration Test Results</Typography>
        {Object.entries(integrationResults.results).map(([service, result]) => (
          <Box key={service} sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
            <Typography variant="body2" sx={{ minWidth: 100, textTransform: 'capitalize' }}>
              {service}:
            </Typography>
            <Typography 
              variant="body2" 
              color={result.success ? 'success.main' : 'error.main'}
              sx={{ ml: 1 }}
            >
              {result.success ? '✓ Connected' : '✗ Failed'}
            </Typography>
            {service === 'ollama' && result.models_available !== undefined && (
              <Typography variant="body2" sx={{ ml: 2 }}>
                ({result.models_available} models available)
              </Typography>
            )}
          </Box>
        ))}
        <Typography 
          variant="body2" 
          color={integrationResults.overall_health ? 'success.main' : 'warning.main'}
          sx={{ mt: 1, fontWeight: 'bold' }}
        >
          Overall Health: {integrationResults.overall_health ? 'Good' : 'Issues Detected'}
        </Typography>
      </Paper>
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!settings) {
    return (
      <Box>
        <Alert severity="error">Failed to load settings</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Settings</Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {successMessage && <Alert severity="success" sx={{ mb: 2 }}>{successMessage}</Alert>}
      
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6">User Preferences</Typography>
        <FormControl fullWidth margin="dense">
          <InputLabel>Theme</InputLabel>
          <Select name="theme" value={settings.theme || 'light'} onChange={handleChange}>
            <MenuItem value="light">Light</MenuItem>
            <MenuItem value="dark">Dark</MenuItem>
          </Select>
        </FormControl>
        <FormControl fullWidth margin="dense">
          <InputLabel>Language</InputLabel>
          <Select name="language" value={settings.language || 'en'} onChange={handleChange}>
            <MenuItem value="en">English</MenuItem>
            <MenuItem value="es">Spanish</MenuItem>
          </Select>
        </FormControl>

        <Typography variant="h6" sx={{ mt: 2 }}>LLM Configuration</Typography>
        <FormControl fullWidth margin="dense">
          <InputLabel>LLM Provider</InputLabel>
          <Select name="llm_provider" value={settings.llm_provider || 'openai'} onChange={handleChange}>
            <MenuItem value="openai">OpenAI</MenuItem>
            <MenuItem value="ollama">Ollama</MenuItem>
          </Select>
        </FormControl>
        <TextField margin="dense" name="llm_model" label="LLM Model" type="text" fullWidth value={settings.llm_model || ''} onChange={handleChange} />
        <TextField margin="dense" name="llm_api_key" label="LLM API Key" type="password" fullWidth value={settings.llm_api_key || ''} onChange={handleChange} />
        <TextField margin="dense" name="llm_api_base" label="LLM API Base URL" type="text" fullWidth value={settings.llm_api_base || ''} onChange={handleChange} />
        
        <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
          <Button 
            variant="outlined" 
            onClick={testLLMConnection}
            size="small"
          >
            Test LLM Connection
          </Button>
          <Button 
            variant="outlined" 
            onClick={testIntegrations}
            disabled={testingIntegrations}
            size="small"
          >
            {testingIntegrations ? <CircularProgress size={20} /> : 'Test All Integrations'}
          </Button>
        </Box>

        <Typography variant="h6" sx={{ mt: 2 }}>Notifications</Typography>
        <FormControlLabel control={<Switch name="email_notifications" checked={settings.email_notifications || false} onChange={handleChange} />} label="Email Notifications" />
        <FormControlLabel control={<Switch name="task_completion_notifications" checked={settings.task_completion_notifications || false} onChange={handleChange} />} label="Task Completion" />
        <FormControlLabel control={<Switch name="project_updates_notifications" checked={settings.project_updates_notifications || false} onChange={handleChange} />} label="Project Updates" />

        <Button 
          variant="contained" 
          sx={{ mt: 2 }} 
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? <CircularProgress size={20} /> : 'Save Settings'}
        </Button>
      </Paper>
      
      {renderIntegrationResults()}
    </Box>
  );
}