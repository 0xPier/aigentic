import { useState, useEffect } from 'react';
import { Box, Button, Typography, Table, TableBody, TableCell, TableHead, TableRow, Paper, Dialog, DialogActions, DialogContent, DialogTitle, TextField } from '@mui/material';
import { apiCall } from '../src/utils/api';

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [open, setOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [isEdit, setIsEdit] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function fetchProjects() {
      try {
        setError(null);
        const data = await apiCall('/projects/');
        setProjects(data);
      } catch (error) {
        setError('Failed to load projects: ' + error.message);
      } finally {
        setLoading(false);
      }
    }
    fetchProjects();
  }, []);

  const handleOpen = (project = null) => {
    setSelectedProject(project);
    setIsEdit(!!project);
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedProject(null);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      if (selectedProject.id) {
        await apiCall(`/projects/${selectedProject.id}`, {
          method: 'PUT',
          body: JSON.stringify(selectedProject),
        });
      } else {
        await apiCall('/projects/', {
          method: 'POST',
          body: JSON.stringify(selectedProject),
        });
      }
      // Refresh projects list
      const data = await apiCall('/projects/');
      setProjects(data);
      setSelectedProject(null);
    } catch (error) {
      setError('Failed to save project: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      setError(null);
      await apiCall(`/projects/${id}`, { method: 'DELETE' });
      // Refresh projects list
      const data = await apiCall('/projects/');
      setProjects(data);
    } catch (error) {
      setError('Failed to delete project: ' + error.message);
    }
  };

  const handleChange = (e) => {
    setSelectedProject({ ...selectedProject, [e.target.name]: e.target.value });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Projects</Typography>
      <Button variant="contained" onClick={() => handleOpen()}>New Project</Button>
      <Paper sx={{ mt: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {projects.map((project) => (
              <TableRow key={project.id}>
                <TableCell>{project.name}</TableCell>
                <TableCell>{project.description}</TableCell>
                <TableCell>
                  <Button onClick={() => handleOpen(project)}>Edit</Button>
                  <Button onClick={() => handleDelete(project.id)}>Delete</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>{isEdit ? 'Edit Project' : 'New Project'}</DialogTitle>
        <DialogContent>
          <TextField autoFocus margin="dense" name="name" label="Name" type="text" fullWidth value={selectedProject?.name || ''} onChange={handleChange} />
          <TextField margin="dense" name="description" label="Description" type="text" fullWidth multiline rows={4} value={selectedProject?.description || ''} onChange={handleChange} />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSave}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}