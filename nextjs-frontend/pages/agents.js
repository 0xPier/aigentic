import { useState, useEffect } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableHead, TableRow, Paper, Card, CardContent, Grid } from '@mui/material';
import { apiCall } from '../src/utils/api';

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [performance, setPerformance] = useState([]);

  useEffect(() => {
    fetchAgents();
    fetchPerformance();
  }, []);

  const fetchAgents = async () => {
    try {
      const data = await apiCall('/agents/available');
      setAgents(data.agents);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const fetchPerformance = async () => {
    try {
      const data = await apiCall('/agents/performance');
      setPerformance(data.agent_performance);
    } catch (error) {
      console.error('Error fetching performance:', error);
    }
  };

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