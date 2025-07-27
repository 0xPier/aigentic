import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  LinearProgress,
  Fab,
  Chip,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Folder as FolderIcon,
  Assignment as TaskIcon,
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';

import { fetchProjects, projectsAPI } from '../../services/api';

function ProjectCard({ project, onEdit, onDelete }) {
  const [anchorEl, setAnchorEl] = useState(null);

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleEdit = () => {
    onEdit(project);
    handleMenuClose();
  };

  const handleDelete = () => {
    onDelete(project.id);
    handleMenuClose();
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box display="flex" alignItems="center" mb={1}>
            <FolderIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6" component="div">
              {project.name}
            </Typography>
          </Box>
          <IconButton size="small" onClick={handleMenuOpen}>
            <MoreVertIcon />
          </IconButton>
        </Box>
        
        <Typography variant="body2" color="textSecondary" paragraph>
          {project.description}
        </Typography>

        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <Chip
            icon={<TaskIcon />}
            label={`${project.task_count || 0} tasks`}
            size="small"
            variant="outlined"
          />
          <Chip
            label={project.status || 'active'}
            size="small"
            color={project.status === 'completed' ? 'success' : 'default'}
          />
        </Box>

        <Typography variant="caption" color="textSecondary">
          Created: {new Date(project.created_at).toLocaleDateString()}
        </Typography>
      </CardContent>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleEdit}>
          <EditIcon sx={{ mr: 1 }} fontSize="small" />
          Edit
        </MenuItem>
        <MenuItem onClick={handleDelete}>
          <DeleteIcon sx={{ mr: 1 }} fontSize="small" />
          Delete
        </MenuItem>
      </Menu>
    </Card>
  );
}

function ProjectDialog({ open, onClose, project, onSubmit, mode = 'create' }) {
  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    defaultValues: {
      name: project?.name || '',
      description: project?.description || '',
      status: project?.status || 'active',
    },
  });

  React.useEffect(() => {
    if (project && mode === 'edit') {
      reset({
        name: project.name,
        description: project.description,
        status: project.status,
      });
    }
  }, [project, mode, reset]);

  const handleFormSubmit = (data) => {
    onSubmit(data);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {mode === 'create' ? 'Create New Project' : 'Edit Project'}
      </DialogTitle>
      <form onSubmit={handleSubmit(handleFormSubmit)}>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2}>
            <Controller
              name="name"
              control={control}
              rules={{ required: 'Project name is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Project Name"
                  fullWidth
                  error={!!errors.name}
                  helperText={errors.name?.message}
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
              name="status"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Status"
                  fullWidth
                >
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="on_hold">On Hold</MenuItem>
                  <MenuItem value="archived">Archived</MenuItem>
                </TextField>
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

function Projects() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [dialogMode, setDialogMode] = useState('create');
  const [error, setError] = useState('');

  const queryClient = useQueryClient();

  // Fetch projects
  const {
    data: projects,
    isLoading: projectsLoading,
    error: projectsError,
  } = useQuery('projects', fetchProjects);

  // Create project mutation
  const createProjectMutation = useMutation(projectsAPI.createProject, {
    onSuccess: () => {
      queryClient.invalidateQueries('projects');
      setError('');
    },
    onError: (error) => {
      setError(error.response?.data?.detail || 'Failed to create project');
    },
  });

  // Update project mutation
  const updateProjectMutation = useMutation(
    ({ projectId, data }) => projectsAPI.updateProject(projectId, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('projects');
        setError('');
      },
      onError: (error) => {
        setError(error.response?.data?.detail || 'Failed to update project');
      },
    }
  );

  // Delete project mutation
  const deleteProjectMutation = useMutation(projectsAPI.deleteProject, {
    onSuccess: () => {
      queryClient.invalidateQueries('projects');
      setError('');
    },
    onError: (error) => {
      setError(error.response?.data?.detail || 'Failed to delete project');
    },
  });

  const handleCreateProject = () => {
    setSelectedProject(null);
    setDialogMode('create');
    setDialogOpen(true);
  };

  const handleEditProject = (project) => {
    setSelectedProject(project);
    setDialogMode('edit');
    setDialogOpen(true);
  };

  const handleDeleteProject = async (projectId) => {
    if (window.confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      deleteProjectMutation.mutate(projectId);
    }
  };

  const handleProjectSubmit = (data) => {
    if (dialogMode === 'create') {
      createProjectMutation.mutate(data);
    } else {
      updateProjectMutation.mutate({ projectId: selectedProject.id, data });
    }
  };

  if (projectsError) {
    return (
      <Alert severity="error">
        Failed to load projects. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Projects</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateProject}
        >
          Create Project
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {projectsLoading && <LinearProgress sx={{ mb: 2 }} />}

      {projects?.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <FolderIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="textSecondary" gutterBottom>
            No projects yet
          </Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            Create your first project to organize your AI consultancy tasks.
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateProject}
          >
            Create Your First Project
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {projects?.map((project) => (
            <Grid item xs={12} sm={6} md={4} key={project.id}>
              <ProjectCard
                project={project}
                onEdit={handleEditProject}
                onDelete={handleDeleteProject}
              />
            </Grid>
          ))}
        </Grid>
      )}

      <ProjectDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        project={selectedProject}
        onSubmit={handleProjectSubmit}
        mode={dialogMode}
      />

      <Fab
        color="primary"
        aria-label="add project"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={handleCreateProject}
      >
        <AddIcon />
      </Fab>
    </Box>
  );
}

export default Projects;
