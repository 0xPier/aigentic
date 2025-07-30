import { useState, useEffect } from 'react';
import { Box, Button, Typography, Paper, TextField, Select, MenuItem, FormControl, InputLabel, Switch, FormControlLabel } from '@mui/material';
import { apiCall } from '../src/utils/api';

export default function Settings() {
  const [settings, setSettings] = useState(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const data = await apiCall('/settings');
      setSettings(data);
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  };

  const handleSave = async () => {
    try {
      await apiCall('/settings', {
        method: 'PUT',
        body: JSON.stringify(settings),
      });
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings({ ...settings, [name]: type === 'checkbox' ? checked : value });
  };

  if (!settings) return <p>Loading...</p>;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Settings</Typography>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6">User Preferences</Typography>
        <FormControl fullWidth margin="dense">
          <InputLabel>Theme</InputLabel>
          <Select name="theme" value={settings.theme} onChange={handleChange}>
            <MenuItem value="light">Light</MenuItem>
            <MenuItem value="dark">Dark</MenuItem>
          </Select>
        </FormControl>
        <FormControl fullWidth margin="dense">
          <InputLabel>Language</InputLabel>
          <Select name="language" value={settings.language} onChange={handleChange}>
            <MenuItem value="en">English</MenuItem>
            <MenuItem value="es">Spanish</MenuItem>
          </Select>
        </FormControl>

        <Typography variant="h6" sx={{ mt: 2 }}>LLM Configuration</Typography>
        <FormControl fullWidth margin="dense">
          <InputLabel>LLM Provider</InputLabel>
          <Select name="llm_provider" value={settings.llm_provider} onChange={handleChange}>
            <MenuItem value="openai">OpenAI</MenuItem>
            <MenuItem value="ollama">Ollama</MenuItem>
          </Select>
        </FormControl>
        <TextField margin="dense" name="llm_model" label="LLM Model" type="text" fullWidth value={settings.llm_model} onChange={handleChange} />
        <TextField margin="dense" name="llm_api_key" label="LLM API Key" type="password" fullWidth value={settings.llm_api_key} onChange={handleChange} />
        <TextField margin="dense" name="llm_api_base" label="LLM API Base URL" type="text" fullWidth value={settings.llm_api_base} onChange={handleChange} />

        <Typography variant="h6" sx={{ mt: 2 }}>Notifications</Typography>
        <FormControlLabel control={<Switch name="email_notifications" checked={settings.email_notifications} onChange={handleChange} />} label="Email Notifications" />
        <FormControlLabel control={<Switch name="task_completion_notifications" checked={settings.task_completion_notifications} onChange={handleChange} />} label="Task Completion" />
        <FormControlLabel control={<Switch name="project_updates_notifications" checked={settings.project_updates_notifications} onChange={handleChange} />} label="Project Updates" />

        <Button variant="contained" sx={{ mt: 2 }} onClick={handleSave}>Save Settings</Button>
      </Paper>
    </Box>
  );
}