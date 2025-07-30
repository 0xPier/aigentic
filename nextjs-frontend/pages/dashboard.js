import { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Grid, CircularProgress, Box, Alert, Button } from '@mui/material';
import { apiCall } from '../src/utils/api';

export default function Dashboard({ showGlobalError }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        setError(null); // Reset error state on new fetch
        const data = await apiCall('/dashboard/');
        setStats(data);
      } catch (error) {
        setError(error.message);
        // Error is now handled through the error state
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, [showGlobalError]);

  const retryFetch = () => {
    setLoading(true);
    setError(null);
    setTimeout(async () => {
      try {
        const data = await apiCall('/dashboard/');
        setStats(data);
        setError(null);
      } catch (error) {
        setError(error.message);
        // Error is now handled through the error state
      } finally {
        setLoading(false);
      }
    }, 100);
  };

  if (loading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>Dashboard</Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
          <CircularProgress />
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>Dashboard</Typography>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load dashboard data: {error}
          <Box sx={{ mt: 1 }}>
            <Button variant="outlined" size="small" onClick={retryFetch}>
              Retry
            </Button>
          </Box>
        </Alert>
        
        {/* Show placeholder dashboard */}
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>Total Tasks</Typography>
                <Typography variant="h5">--</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>Completed Tasks</Typography>
                <Typography variant="h5">--</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>Pending Tasks</Typography>
                <Typography variant="h5">--</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>Failed Tasks</Typography>
                <Typography variant="h5">--</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    );
  }

  if (!stats) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>Dashboard</Typography>
        <Typography>No dashboard data available.</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Dashboard</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Total Tasks</Typography>
              <Typography variant="h5">{stats.total_tasks}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Completed Tasks</Typography>
              <Typography variant="h5">{stats.completed_tasks}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Pending Tasks</Typography>
              <Typography variant="h5">{stats.pending_tasks}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Failed Tasks</Typography>
              <Typography variant="h5">{stats.failed_tasks}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Avg. Execution Time</Typography>
              <Typography variant="h5">{stats.average_execution_time?.toFixed(2) || 0}s</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Tasks This Month</Typography>
              <Typography variant="h5">{stats.tasks_this_month || 0} / {stats.monthly_limit || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Subscription Tier</Typography>
              <Typography variant="h5">{stats.subscription_tier || 'Free'}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}