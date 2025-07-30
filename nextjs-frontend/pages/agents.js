import { useState, useEffect } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableHead, TableRow, Paper, Card, CardContent, Grid } from '@mui/material';
import { apiCall } from '../src/utils/api';

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [performance, setPerformance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchAgents() {
      try {
        setError(null);
        const data = await apiCall('/agents/');
        setAgents(data);
      } catch (error) {
        setError('Failed to load agents: ' + error.message);
      } finally {
        setLoading(false);
      }
    }
    
    async function fetchPerformance() {
      try {
        const data = await apiCall('/agents/performance');
        setPerformance(data.agent_performance || []);
      } catch (error) {
        setError('Failed to load performance data: ' + error.message);
      }
    }

    fetchAgents();
    fetchPerformance();
  }, []);

  if (loading) {
    return <Box>Loading...</Box>;
  }

  if (error) {
    return <Box color="error">{error}</Box>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Agents</Typography>
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {agents.map((agent) => (
          <Grid item xs={12} md={4} key={agent.name}>
            <Card>
              <CardContent>
                <Typography variant="h6">{agent.name}</Typography>
                <Typography color="textSecondary">{agent.description}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Typography variant="h5" gutterBottom>Agent Performance</Typography>
      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Agent</TableCell>
              <TableCell>Total Tasks</TableCell>
              <TableCell>Completed</TableCell>
              <TableCell>Failed</TableCell>
              <TableCell>Success Rate</TableCell>
              <TableCell>Avg. Time (s)</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {performance.map((p) => (
              <TableRow key={p.agent_name}>
                <TableCell>{p.agent_name}</TableCell>
                <TableCell>{p.total_tasks}</TableCell>
                <TableCell>{p.completed_tasks}</TableCell>
                <TableCell>{p.failed_tasks}</TableCell>
                <TableCell>{p.success_rate.toFixed(2)}%</TableCell>
                <TableCell>{p.average_execution_time.toFixed(2)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}