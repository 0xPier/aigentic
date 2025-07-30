import { useState, useEffect } from 'react';
import { Box, Button, Typography, Table, TableBody, TableCell, TableHead, TableRow, Paper, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Switch, FormControlLabel } from '@mui/material';
import { apiCall } from '../src/utils/api';

export default function Integrations() {
  const [integrations, setIntegrations] = useState([]);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({});
  const [isEdit, setIsEdit] = useState(false);

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async () => {
    try {
      const data = await apiCall('/integrations');
      setIntegrations(data);
    } catch (error) {
      console.error('Error fetching integrations:', error);
    }
  };

  const handleOpen = (integration = null) => {
    if (integration) {
      setIsEdit(true);
      setFormData({
        id: integration.id,
        name: integration.integration_type, // Map API response field to form field
        api_key: '', // Do not expose existing key
        is_active: integration.is_active,
      });
    } else {
      setIsEdit(false);
      setFormData({ name: '', api_key: '', is_active: true });
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setFormData({});
  };

  const handleSave = async () => {
    try {
      const { id, ...data } = formData;
      // For edits, don't send an empty api_key if the user didn't enter a new one
      if (isEdit && !data.api_key) {
        delete data.api_key;
      }

      const method = isEdit ? 'PUT' : 'POST';
      const endpoint = isEdit ? `/integrations/${id}` : '/integrations';
      
      await apiCall(endpoint, {
        method,
        body: JSON.stringify(data),
      });

      fetchIntegrations();
      handleClose();
    } catch (error) {
      console.error('Error saving integration:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await apiCall(`/integrations/${id}`, { method: 'DELETE' });
      fetchIntegrations();
    } catch (error) {
      console.error('Error deleting integration:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({ ...formData, [name]: type === 'checkbox' ? checked : value });
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
          <TextField autoFocus margin="dense" name="name" label="Name" type="text" fullWidth value={formData?.name || ''} onChange={handleChange} />
          <TextField margin="dense" name="api_key" label="API Key" type="password" fullWidth value={formData?.api_key || ''} onChange={handleChange} placeholder={isEdit ? "Leave blank to keep existing key" : ""} />
          <FormControlLabel control={<Switch name="is_active" checked={formData?.is_active || false} onChange={handleChange} />} label="Active" />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSave}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
