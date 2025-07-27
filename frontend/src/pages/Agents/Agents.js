import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Avatar,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  Search as SearchIcon,
  Analytics as AnalyticsIcon,
  Create as CreateIcon,
  Share as ShareIcon,
  Image as ImageIcon,
  Recommend as RecommendIcon,
  Slideshow as SlideshowIcon,
  AutoMode as AutoModeIcon,
  Assessment as AssessmentIcon,
  SupportAgent as SupportAgentIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

import { fetchAvailableAgents, fetchAgentPerformance } from '../../services/api';

const agentIcons = {
  'orchestrator': PsychologyIcon,
  'research': SearchIcon,
  'analysis': AnalyticsIcon,
  'content': CreateIcon,
  'social_media': ShareIcon,
  'graphics': ImageIcon,
  'recommendation': RecommendIcon,
  'presentation': SlideshowIcon,
  'automation': AutoModeIcon,
  'reporting': AssessmentIcon,
  'customer_care': SupportAgentIcon,
};

const agentColors = {
  'orchestrator': '#9c27b0',
  'research': '#2196f3',
  'analysis': '#ff9800',
  'content': '#4caf50',
  'social_media': '#e91e63',
  'graphics': '#673ab7',
  'recommendation': '#795548',
  'presentation': '#ff5722',
  'automation': '#607d8b',
  'reporting': '#009688',
  'customer_care': '#3f51b5',
};

function AgentCard({ agent, onViewDetails }) {
  const IconComponent = agentIcons[agent.name.toLowerCase()] || PsychologyIcon;
  const agentColor = agentColors[agent.name.toLowerCase()] || '#757575';

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box display="flex" alignItems="center" mb={2}>
          <Avatar sx={{ bgcolor: agentColor, mr: 2 }}>
            <IconComponent />
          </Avatar>
          <Box>
            <Typography variant="h6" component="div">
              {agent.name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </Typography>
            <Chip
              label={agent.status || 'Available'}
              size="small"
              color={agent.status === 'active' ? 'success' : 'default'}
            />
          </Box>
        </Box>
        
        <Typography variant="body2" color="textSecondary" paragraph>
          {agent.description}
        </Typography>

        <Box mb={2}>
          <Typography variant="subtitle2" gutterBottom>
            Capabilities:
          </Typography>
          <Box display="flex" flexWrap="wrap" gap={0.5}>
            {agent.capabilities?.slice(0, 3).map((capability, index) => (
              <Chip
                key={index}
                label={capability}
                size="small"
                variant="outlined"
              />
            ))}
            {agent.capabilities?.length > 3 && (
              <Chip
                label={`+${agent.capabilities.length - 3} more`}
                size="small"
                variant="outlined"
                color="primary"
              />
            )}
          </Box>
        </Box>

        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="caption" color="textSecondary">
            Tasks completed: {agent.tasks_completed || 0}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Success rate: {Math.round((agent.success_rate || 0) * 100)}%
          </Typography>
        </Box>
      </CardContent>
      
      <CardActions>
        <Button 
          size="small" 
          onClick={() => onViewDetails(agent)}
          startIcon={<InfoIcon />}
        >
          View Details
        </Button>
        <Button 
          size="small" 
          variant="contained"
          onClick={() => window.location.href = `/tasks?agent=${agent.name}`}
        >
          Create Task
        </Button>
      </CardActions>
    </Card>
  );
}

function AgentDetailsDialog({ open, onClose, agent }) {
  if (!agent) return null;

  const IconComponent = agentIcons[agent.name.toLowerCase()] || PsychologyIcon;
  const agentColor = agentColors[agent.name.toLowerCase()] || '#757575';

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center">
          <Avatar sx={{ bgcolor: agentColor, mr: 2 }}>
            <IconComponent />
          </Avatar>
          <Box>
            <Typography variant="h6">
              {agent.name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Agent
            </Typography>
            <Chip
              label={agent.status || 'Available'}
              size="small"
              color={agent.status === 'active' ? 'success' : 'default'}
            />
          </Box>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>
            Description
          </Typography>
          <Typography variant="body1" paragraph>
            {agent.description}
          </Typography>
        </Box>

        <Box mb={3}>
          <Typography variant="h6" gutterBottom>
            Capabilities
          </Typography>
          <List dense>
            {agent.capabilities?.map((capability, index) => (
              <ListItem key={index}>
                <ListItemText primary={capability} />
              </ListItem>
            ))}
          </List>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Typography variant="h6" gutterBottom>
              Performance Stats
            </Typography>
            <Typography variant="body2">
              Tasks Completed: {agent.tasks_completed || 0}
            </Typography>
            <Typography variant="body2">
              Success Rate: {Math.round((agent.success_rate || 0) * 100)}%
            </Typography>
            <Typography variant="body2">
              Avg. Execution Time: {agent.avg_execution_time || 'N/A'}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="h6" gutterBottom>
              Configuration
            </Typography>
            <Typography variant="body2">
              Version: {agent.version || '1.0.0'}
            </Typography>
            <Typography variant="body2">
              Model: {agent.model || 'GPT-4'}
            </Typography>
            <Typography variant="body2">
              Max Tokens: {agent.max_tokens || '4000'}
            </Typography>
          </Grid>
        </Grid>

        {agent.example_queries && (
          <Box mt={3}>
            <Typography variant="h6" gutterBottom>
              Example Queries
            </Typography>
            <List dense>
              {agent.example_queries.map((query, index) => (
                <ListItem key={index}>
                  <ListItemText 
                    primary={query}
                    primaryTypographyProps={{ variant: 'body2', fontStyle: 'italic' }}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        <Button 
          variant="contained"
          onClick={() => {
            onClose();
            window.location.href = `/tasks?agent=${agent.name}`;
          }}
        >
          Create Task with this Agent
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function Agents() {
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Fetch available agents
  const {
    data: agents,
    isLoading: agentsLoading,
    error: agentsError,
  } = useQuery('availableAgents', fetchAvailableAgents);

  // Fetch agent performance
  const {
    data: performance,
    isLoading: performanceLoading,
  } = useQuery('agentPerformance', fetchAgentPerformance);

  const handleViewDetails = (agent) => {
    // Merge performance data if available
    const agentWithPerformance = {
      ...agent,
      ...(performance?.find(p => p.agent_name === agent.name) || {}),
    };
    setSelectedAgent(agentWithPerformance);
    setDetailsOpen(true);
  };

  if (agentsError) {
    return (
      <Alert severity="error">
        Failed to load agents. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          AI Agents
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Explore our specialized AI agents and their capabilities. Each agent is designed for specific tasks and can be combined for complex workflows.
        </Typography>
      </Box>

      {(agentsLoading || performanceLoading) && <LinearProgress sx={{ mb: 2 }} />}

      {agents?.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <PsychologyIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="textSecondary" gutterBottom>
            No agents available
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Agents are currently being initialized. Please try again in a moment.
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {agents?.map((agent) => (
            <Grid item xs={12} sm={6} md={4} key={agent.name}>
              <AgentCard
                agent={agent}
                onViewDetails={handleViewDetails}
              />
            </Grid>
          ))}
        </Grid>
      )}

      <AgentDetailsDialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        agent={selectedAgent}
      />
    </Box>
  );
}

export default Agents;
