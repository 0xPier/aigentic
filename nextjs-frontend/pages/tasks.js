import { useState, useEffect } from 'react';
import { Box, Button, Typography, Table, TableBody, TableCell, TableHead, TableRow, Paper, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { apiCall } from '../src/utils/api';

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [open, setOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [isEdit, setIsEdit] = useState(false);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const data = await apiCall('/tasks');
      setTasks(data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const handleOpen = (task = null) => {
    setSelectedTask(task);
    setIsEdit(!!task);
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedTask(null);
  };

  const handleSave = async () => {
    try {
      const method = isEdit ? 'PUT' : 'POST';
      const endpoint = isEdit ? `/tasks/${selectedTask.id}` : '/tasks';
      await apiCall(endpoint, {
        method,
        body: JSON.stringify(selectedTask),
      });
      
      fetchTasks();
      handleClose();
    } catch (error) {
      console.error('Error saving task:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await apiCall(`/tasks/${id}`, { method: 'DELETE' });
      fetchTasks();
    } catch (error) {
      console.error('Error deleting task:', error);
    }
  };

  const handleChange = (e) => {
    setSelectedTask({ ...selectedTask, [e.target.name]: e.target.value });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Tasks</Typography>
      <Button variant="contained" onClick={() => handleOpen()}>New Task</Button>
      <Paper sx={{ mt: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Priority</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map((task) => (
              <TableRow key={task.id}>
                <TableCell>{task.title}</TableCell>
                <TableCell>{task.task_type}</TableCell>
                <TableCell>{task.priority}</TableCell>
                <TableCell>{task.status}</TableCell>
                <TableCell>
                  <Button onClick={() => handleOpen(task)}>Edit</Button>
                  <Button onClick={() => handleDelete(task.id)}>Delete</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>{isEdit ? 'Edit Task' : 'New Task'}</DialogTitle>
        <DialogContent>
          <TextField autoFocus margin="dense" name="title" label="Title" type="text" fullWidth value={selectedTask?.title || ''} onChange={handleChange} />
          <TextField margin="dense" name="description" label="Description" type="text" fullWidth multiline rows={4} value={selectedTask?.description || ''} onChange={handleChange} />
          <TextField margin="dense" name="query" label="Query" type="text" fullWidth value={selectedTask?.query || ''} onChange={handleChange} />
          <FormControl fullWidth margin="dense">
            <InputLabel>Type</InputLabel>
            <Select name="task_type" value={selectedTask?.task_type || ''} onChange={handleChange}>
              <MenuItem value="research">Research</MenuItem>
              <MenuItem value="writing">Writing</MenuItem>
              <MenuItem value="analysis">Analysis</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Priority</InputLabel>
            <Select name="priority" value={selectedTask?.priority || ''} onChange={handleChange}>
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="high">High</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSave}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}