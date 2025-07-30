import { useState, useEffect } from 'react';
import { Box, Button, Typography, Table, TableBody, TableCell, TableHead, TableRow, Paper, Dialog, DialogActions, DialogContent, DialogTitle, TextField } from '@mui/material';
import { apiCall } from '../src/utils/api';

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [open, setOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [isEdit, setIsEdit] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const data = await apiCall('/projects');
      setProjects(data);
    } catch (error) {
      console.error('Error fetching projects:', error);
    }
  };

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
    try {
      const method = isEdit ? 'PUT' : 'POST';
      const endpoint = isEdit ? `/projects/${selectedProject.id}` : '/projects';
      await apiCall(endpoint, {
        method,
        body: JSON.stringify(selectedProject),
      });

      fetchProjects();
      handleClose();
    } catch (error) {
      console.error('Error saving project:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await apiCall(`/projects/${id}`, { method: 'DELETE' });
      fetchProjects();
    } catch (error) {
      console.error('Error deleting project:', error);
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