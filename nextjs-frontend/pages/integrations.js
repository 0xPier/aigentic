import { useState, useEffect } from 'react';
import { Box, Button, Typography, Table, TableBody, TableCell, TableHead, TableRow, Paper, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Switch, FormControlLabel } from '@mui/material';
import { apiCall } from '../src/utils/api';

export default function Integrations() {
  const [integrations, setIntegrations] = useState([]);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({});
  const [isEdit, setIsEdit] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [editingIntegration, setEditingIntegration] = useState(null);

  useEffect(() => {
    async function fetchIntegrations() {
      try {
        setError(null);
        const data = await apiCall('/integrations/');
        setIntegrations(data);
      } catch (error) {
        setError('Failed to load integrations: ' + error.message);
      } finally {
        setLoading(false);
      }
    }
    fetchIntegrations();
  }, []);

  const handleOpen = (integration = null) => {
    if (integration) {
      setIsEdit(true);
      setEditingIntegration({
        id: integration.id,
        name: integration.integration_type, // Map API response field to form field
        api_key: '', // Do not expose existing key
        is_active: integration.is_active,
      });
    } else {
      setIsEdit(false);
      setEditingIntegration({ name: '', api_key: '', is_active: true });
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingIntegration(null);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const saveData = { ...editingIntegration };
      // For edits, don't send an empty api_key if the user didn't enter a new one
      if (editingIntegration.id && !saveData.api_key) {
        delete saveData.api_key;
      }
      
      if (editingIntegration.id) {
        await apiCall(`/integrations/${editingIntegration.id}`, {
          method: 'PUT',
          body: JSON.stringify(saveData),
        });
      } else {
        await apiCall('/integrations/', {
          method: 'POST',
          body: JSON.stringify(saveData),
        });
      }
      // Refresh integrations list
      const data = await apiCall('/integrations/');
      setIntegrations(data);
      setEditingIntegration(null);
    } catch (error) {
      setError('Failed to save integration: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      setError(null);
      await apiCall(`/integrations/${id}`, { method: 'DELETE' });
      // Refresh integrations list
      const data = await apiCall('/integrations/');
      setIntegrations(data);
    } catch (error) {
      setError('Failed to delete integration: ' + error.message);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setEditingIntegration({ ...editingIntegration, [name]: type === 'checkbox' ? checked : value });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Integrations</Typography>
      <Button variant="contained" onClick={() => handleOpen()}>New Integration</Button>
      <Paper sx={{ mt: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Active</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {integrations.map((integration) => (
              <TableRow key={integration.id}>
                <TableCell>{integration.integration_type}</TableCell>
                <TableCell>{integration.is_active ? 'Yes' : 'No'}</TableCell>
                <TableCell>
                  <Button onClick={() => handleOpen(integration)}>Edit</Button>
                  <Button onClick={() => handleDelete(integration.id)}>Delete</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>{isEdit ? 'Edit Integration' : 'New Integration'}</DialogTitle>
        <DialogContent>
          <TextField autoFocus margin="dense" name="name" label="Name" type="text" fullWidth value={editingIntegration?.name || ''} onChange={handleChange} />
          <TextField margin="dense" name="api_key" label="API Key" type="password" fullWidth value={editingIntegration?.api_key || ''} onChange={handleChange} placeholder={isEdit ? "Leave blank to keep existing key" : ""} />
          <FormControlLabel control={<Switch name="is_active" checked={editingIntegration?.is_active || false} onChange={handleChange} />} label="Active" />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : 'Save'}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
