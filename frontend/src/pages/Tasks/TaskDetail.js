import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Chip,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ArrowBack,
  Edit,
  Delete,
  PlayArrow,
  Pause,
  CheckCircle,
  Schedule,
  Person,
  CalendarToday
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { tasksAPI } from '../../services/api';

const TaskDetail = () => {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: task, isLoading, error } = useQuery(
    ['task', taskId],
    () => tasksAPI.getTask(taskId),
    {
      enabled: !!taskId
    }
  );

  const updateTaskMutation = useMutation(
    ({ taskId, updates }) => tasksAPI.updateTask(taskId, updates),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['task', taskId]);
        queryClient.invalidateQueries(['tasks']);
      }
    }
  );

  const deleteTaskMutation = useMutation(
    (taskId) => tasksAPI.deleteTask(taskId),
    {
      onSuccess: () => {
        navigate('/tasks');
      }
    }
  );

  const handleStatusChange = (newStatus) => {
    updateTaskMutation.mutate({
      taskId,
      updates: { status: newStatus }
    });
  };

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      deleteTaskMutation.mutate(taskId);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle />;
      case 'in_progress':
        return <PlayArrow />;
      case 'pending':
        return <Schedule />;
      default:
        return <Schedule />;
    }
  };

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">
          Error loading task: {error.message}
        </Alert>
      </Container>
    );
  }

  if (!task) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="warning">
          Task not found
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/tasks')}
          sx={{ mb: 2 }}
        >
          Back to Tasks
        </Button>
      </Box>

      <Paper elevation={3} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" component="h1" gutterBottom>
              {task.title}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Chip
                icon={getStatusIcon(task.status)}
                label={task.status?.replace('_', ' ').toUpperCase()}
                color={getStatusColor(task.status)}
                variant="outlined"
              />
              {task.priority && (
                <Chip
                  label={`Priority: ${task.priority}`}
                  color={task.priority === 'high' ? 'error' : task.priority === 'medium' ? 'warning' : 'default'}
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Edit Task">
              <IconButton onClick={() => navigate(`/tasks/${taskId}/edit`)}>
                <Edit />
              </IconButton>
            </Tooltip>
            <Tooltip title="Delete Task">
              <IconButton onClick={handleDelete} color="error">
                <Delete />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Description
                </Typography>
                <Typography variant="body1" paragraph>
                  {task.description || 'No description provided'}
                </Typography>

                {task.result && (
                  <>
                    <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                      Result
                    </Typography>
                    <Typography variant="body1" paragraph>
                      {task.result}
                    </Typography>
                  </>
                )}

                {task.error && (
                  <>
                    <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                      Error
                    </Typography>
                    <Alert severity="error">
                      {task.error}
                    </Alert>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Task Details
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Person sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2">
                    Agent: {task.agent_type || 'N/A'}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CalendarToday sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2">
                    Created: {task.created_at ? new Date(task.created_at).toLocaleDateString() : 'N/A'}
                  </Typography>
                </Box>

                {task.updated_at && (
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <CalendarToday sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2">
                      Updated: {new Date(task.updated_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                )}

                <Divider sx={{ my: 2 }} />

                <Typography variant="subtitle2" gutterBottom>
                  Actions
                </Typography>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {task.status === 'pending' && (
                    <Button
                      variant="contained"
                      startIcon={<PlayArrow />}
                      onClick={() => handleStatusChange('in_progress')}
                      disabled={updateTaskMutation.isLoading}
                    >
                      Start Task
                    </Button>
                  )}
                  
                  {task.status === 'in_progress' && (
                    <>
                      <Button
                        variant="contained"
                        startIcon={<Pause />}
                        onClick={() => handleStatusChange('pending')}
                        disabled={updateTaskMutation.isLoading}
                      >
                        Pause Task
                      </Button>
                      <Button
                        variant="contained"
                        color="success"
                        startIcon={<CheckCircle />}
                        onClick={() => handleStatusChange('completed')}
                        disabled={updateTaskMutation.isLoading}
                      >
                        Mark Complete
                      </Button>
                    </>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default TaskDetail;
