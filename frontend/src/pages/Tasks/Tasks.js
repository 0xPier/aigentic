import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Alert,
  LinearProgress,
  Fab,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  PlayArrow as ExecuteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';

import { fetchTasks, tasksAPI, fetchAvailableAgents, executeAgentTask } from '../../services/api';

function TaskStatusChip({ status }) {
  const getStatusProps = (status) => {
    switch (status) {
      case 'completed':
        return { color: 'success', label: 'Completed' };
      case 'in_progress':
        return { color: 'warning', label: 'In Progress' };
      case 'failed':
        return { color: 'error', label: 'Failed' };
      case 'pending':
        return { color: 'default', label: 'Pending' };
      default:
        return { color: 'default', label: status };
    }
  };

  const props = getStatusProps(status);
  
  return (
    <Chip
      label={props.label}
      color={props.color}
      size="small"
    />
  );
}

function TaskDialog({ open, onClose, task, agents, onSubmit, mode = 'create' }) {
  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    defaultValues: {
      title: task?.title || '',
      description: task?.description || '',
      agent_name: task?.agent_name || '',
      priority: task?.priority || 'medium',
      project_id: task?.project_id || '',
    },
  });

  React.useEffect(() => {
    if (task && mode === 'edit') {
      reset({
        title: task.title,
        description: task.description,
        agent_name: task.agent_name,
        priority: task.priority,
        project_id: task.project_id,
      });
    }
  }, [task, mode, reset]);

  const handleFormSubmit = (data) => {
    onSubmit(data);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {mode === 'create' ? 'Create New Task' : 'Edit Task'}
      </DialogTitle>
      <form onSubmit={handleSubmit(handleFormSubmit)}>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2}>
            <Controller
              name="title"
              control={control}
              rules={{ required: 'Title is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Task Title"
                  fullWidth
                  error={!!errors.title}
                  helperText={errors.title?.message}
                />
              )}
            />
            
            <Controller
              name="description"
              control={control}
              rules={{ required: 'Description is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Description"
                  multiline
                  rows={4}
                  fullWidth
                  error={!!errors.description}
                  helperText={errors.description?.message}
                />
              )}
            />

            <Controller
              name="agent_name"
              control={control}
              rules={{ required: 'Agent is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Agent"
                  fullWidth
                  error={!!errors.agent_name}
                  helperText={errors.agent_name?.message}
                >
                  {agents?.map((agent) => (
                    <MenuItem key={agent.name} value={agent.name}>
                      {agent.name} - {agent.description}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />

            <Controller
              name="priority"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Priority"
                  fullWidth
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="urgent">Urgent</MenuItem>
                </TextField>
              )}
            />

            <Controller
              name="project_id"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Project ID (Optional)"
                  fullWidth
                  helperText="Link this task to a specific project"
                />
              )}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained">
            {mode === 'create' ? 'Create' : 'Update'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

function Tasks() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [dialogMode, setDialogMode] = useState('create');
  const [error, setError] = useState('');

  const queryClient = useQueryClient();

  // Fetch tasks
  const {
    data: tasksData,
    isLoading: tasksLoading,
    error: tasksError,
  } = useQuery(['tasks', page, rowsPerPage], () =>
    fetchTasks({ skip: page * rowsPerPage, limit: rowsPerPage })
  );

  // Fetch available agents
  const {
    data: agents,
    isLoading: agentsLoading,
  } = useQuery('availableAgents', fetchAvailableAgents);

  // Create task mutation
  const createTaskMutation = useMutation(tasksAPI.createTask, {
    onSuccess: () => {
      queryClient.invalidateQueries('tasks');
      setError('');
    },
    onError: (error) => {
      setError(error.response?.data?.detail || 'Failed to create task');
    },
  });

  // Update task mutation
  const updateTaskMutation = useMutation(
    ({ taskId, data }) => tasksAPI.updateTask(taskId, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('tasks');
        setError('');
      },
      onError: (error) => {
        setError(error.response?.data?.detail || 'Failed to update task');
      },
    }
  );

  // Delete task mutation
  const deleteTaskMutation = useMutation(tasksAPI.deleteTask, {
    onSuccess: () => {
      queryClient.invalidateQueries('tasks');
      setError('');
    },
    onError: (error) => {
      setError(error.response?.data?.detail || 'Failed to delete task');
    },
  });

  // Execute task mutation
  const executeTaskMutation = useMutation(executeAgentTask, {
    onSuccess: () => {
      queryClient.invalidateQueries('tasks');
      setError('');
    },
    onError: (error) => {
      setError(error.response?.data?.detail || 'Failed to execute task');
    },
  });

  const handleCreateTask = () => {
    setSelectedTask(null);
    setDialogMode('create');
    setDialogOpen(true);
  };

  const handleEditTask = (task) => {
    setSelectedTask(task);
    setDialogMode('edit');
    setDialogOpen(true);
  };

  const handleDeleteTask = async (taskId) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      deleteTaskMutation.mutate(taskId);
    }
  };

  const handleExecuteTask = async (task) => {
    executeTaskMutation.mutate({
      agent_name: task.agent_name,
      query: task.description,
      context: { task_id: task.id },
    });
  };

  const handleTaskSubmit = (data) => {
    if (dialogMode === 'create') {
      createTaskMutation.mutate(data);
    } else {
      updateTaskMutation.mutate({ taskId: selectedTask.id, data });
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (tasksError) {
    return (
      <Alert severity="error">
        Failed to load tasks. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Tasks</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateTask}
          disabled={agentsLoading}
        >
          Create Task
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper>
        {tasksLoading && <LinearProgress />}
        
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Agent</TableCell>
                <TableCell>Priority</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tasksData?.items?.map((task) => (
                <TableRow key={task.id}>
                  <TableCell>
                    <Typography variant="subtitle2">{task.title}</Typography>
                    <Typography variant="body2" color="textSecondary" noWrap>
                      {task.description}
                    </Typography>
                  </TableCell>
                  <TableCell>{task.agent_name}</TableCell>
                  <TableCell>
                    <Chip
                      label={task.priority}
                      size="small"
                      color={
                        task.priority === 'urgent' ? 'error' :
                        task.priority === 'high' ? 'warning' :
                        task.priority === 'medium' ? 'info' : 'default'
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <TaskStatusChip status={task.status} />
                  </TableCell>
                  <TableCell>
                    {new Date(task.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton size="small">
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit Task">
                      <IconButton 
                        size="small" 
                        onClick={() => handleEditTask(task)}
                        disabled={task.status === 'in_progress'}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Execute Task">
                      <IconButton 
                        size="small" 
                        onClick={() => handleExecuteTask(task)}
                        disabled={task.status === 'in_progress' || executeTaskMutation.isLoading}
                      >
                        <ExecuteIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Task">
                      <IconButton 
                        size="small" 
                        onClick={() => handleDeleteTask(task.id)}
                        disabled={task.status === 'in_progress'}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              )) || (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="textSecondary">
                      No tasks found. Create your first task to get started!
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={tasksData?.total || 0}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>

      <TaskDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        task={selectedTask}
        agents={agents}
        onSubmit={handleTaskSubmit}
        mode={dialogMode}
      />

      <Fab
        color="primary"
        aria-label="refresh"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => queryClient.invalidateQueries('tasks')}
      >
        <RefreshIcon />
      </Fab>
    </Box>
  );
}

export default Tasks;
