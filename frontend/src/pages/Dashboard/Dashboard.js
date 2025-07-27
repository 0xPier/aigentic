import React from 'react';
import { useQuery } from 'react-query';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  Alert,
} from '@mui/material';
import {
  Assignment as TaskIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Error as ErrorIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

import { useAuth } from '../../contexts/AuthContext';
import { fetchDashboardStats, fetchRecentTasks } from '../../services/api';

function StatCard({ title, value, icon, color = 'primary', subtitle }) {
  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="textSecondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box color={`${color}.main`}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

function TaskStatusChip({ status }) {
  const getStatusProps = (status) => {
    switch (status) {
      case 'completed':
        return { color: 'success', icon: <CheckCircleIcon /> };
      case 'in_progress':
        return { color: 'warning', icon: <ScheduleIcon /> };
      case 'failed':
        return { color: 'error', icon: <ErrorIcon /> };
      default:
        return { color: 'default', icon: <ScheduleIcon /> };
    }
  };

  const props = getStatusProps(status);
  
  return (
    <Chip
      label={status.replace('_', ' ').toUpperCase()}
      color={props.color}
      size="small"
      icon={props.icon}
    />
  );
}

function Dashboard() {
  const { user } = useAuth();

  const {
    data: dashboardStats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery('dashboardStats', fetchDashboardStats);

  const {
    data: recentTasks,
    isLoading: tasksLoading,
    error: tasksError,
  } = useQuery('recentTasks', () => fetchRecentTasks({ limit: 5 }));

  // Mock data for charts
  const performanceData = [
    { name: 'Mon', tasks: 4, success: 3 },
    { name: 'Tue', tasks: 6, success: 5 },
    { name: 'Wed', tasks: 8, success: 7 },
    { name: 'Thu', tasks: 5, success: 4 },
    { name: 'Fri', tasks: 7, success: 6 },
    { name: 'Sat', tasks: 3, success: 3 },
    { name: 'Sun', tasks: 2, success: 2 },
  ];

  const agentUsageData = [
    { name: 'Research', usage: 25 },
    { name: 'Content', usage: 20 },
    { name: 'Analysis', usage: 18 },
    { name: 'Social Media', usage: 15 },
    { name: 'Graphics', usage: 12 },
    { name: 'Reporting', usage: 10 },
  ];

  if (statsError || tasksError) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load dashboard data. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Welcome Section */}
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          Welcome back, {user?.full_name || user?.username}!
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Here's an overview of your AI consultancy platform activity.
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Tasks"
            value={dashboardStats?.total_tasks || 0}
            icon={<TaskIcon fontSize="large" />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Completed Tasks"
            value={dashboardStats?.completed_tasks || 0}
            icon={<CheckCircleIcon fontSize="large" />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Success Rate"
            value={`${Math.round((dashboardStats?.completed_tasks / dashboardStats?.total_tasks * 100) || 0)}%`}
            icon={<TrendingUpIcon fontSize="large" />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg. Execution Time"
            value={`${Math.round(dashboardStats?.average_execution_time || 0)}s`}
            icon={<SpeedIcon fontSize="large" />}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* Usage Progress */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Monthly Usage
            </Typography>
            <Box display="flex" alignItems="center" mb={1}>
              <Typography variant="body2" color="textSecondary" sx={{ minWidth: 120 }}>
                Tasks Used: {dashboardStats?.tasks_this_month || 0} / {dashboardStats?.monthly_limit || 10}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={(dashboardStats?.tasks_this_month / dashboardStats?.monthly_limit * 100) || 0}
              sx={{ height: 8, borderRadius: 4 }}
            />
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Subscription: {dashboardStats?.subscription_tier || 'Free'}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box display="flex" flexDirection="column" gap={1}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                fullWidth
                onClick={() => window.location.href = '/tasks'}
              >
                Create New Task
              </Button>
              <Button
                variant="outlined"
                fullWidth
                onClick={() => window.location.href = '/projects'}
              >
                View Projects
              </Button>
              <Button
                variant="outlined"
                fullWidth
                onClick={() => window.location.href = '/agents'}
              >
                Explore Agents
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Weekly Performance
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="tasks" stroke="#1976d2" strokeWidth={2} />
                <Line type="monotone" dataKey="success" stroke="#2e7d32" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Agent Usage
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={agentUsageData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={80} />
                <Tooltip />
                <Bar dataKey="usage" fill="#1976d2" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Tasks */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Recent Tasks
        </Typography>
        {tasksLoading ? (
          <LinearProgress />
        ) : (
          <List>
            {recentTasks?.slice(0, 5).map((task) => (
              <ListItem key={task.id} divider>
                <ListItemIcon>
                  <TaskIcon />
                </ListItemIcon>
                <ListItemText
                  primary={task.title}
                  secondary={`Created: ${new Date(task.created_at).toLocaleDateString()}`}
                />
                <TaskStatusChip status={task.status} />
              </ListItem>
            )) || (
              <Typography color="textSecondary" sx={{ p: 2 }}>
                No recent tasks found. Create your first task to get started!
              </Typography>
            )}
          </List>
        )}
      </Paper>
    </Box>
  );
}

export default Dashboard;
