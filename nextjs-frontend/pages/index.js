import { Box, Typography, Card, CardContent, Grid, Button } from '@mui/material';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();

  const handleNavigation = (path) => {
    console.log('Navigating to:', path);
    router.push(path);
  };

  return (
    <Box>
      <Typography variant="h3" gutterBottom>
        Welcome to AI Agent Platform
      </Typography>
      <Typography variant="h6" color="textSecondary" gutterBottom sx={{ mb: 4 }}>
        Manage your AI agents, tasks, and projects from one central platform.
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card 
            sx={{ 
              height: '100%',
              '&:hover': { 
                transform: 'translateY(-2px)',
                boxShadow: 3 
              },
              transition: 'all 0.2s'
            }}
          >
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Tasks
              </Typography>
              <Typography color="textSecondary" sx={{ flexGrow: 1, mb: 2 }}>
                Create and manage AI-powered tasks
              </Typography>
              <Button 
                variant="contained" 
                color="primary"
                fullWidth
                onClick={() => handleNavigation('/tasks')}
              >
                View Tasks
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card 
            sx={{ 
              height: '100%',
              '&:hover': { 
                transform: 'translateY(-2px)',
                boxShadow: 3 
              },
              transition: 'all 0.2s'
            }}
          >
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Agents
              </Typography>
              <Typography color="textSecondary" sx={{ flexGrow: 1, mb: 2 }}>
                Monitor your AI agents and their performance
              </Typography>
              <Button 
                variant="contained" 
                color="primary"
                fullWidth
                onClick={() => handleNavigation('/agents')}
              >
                View Agents
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card 
            sx={{ 
              height: '100%',
              '&:hover': { 
                transform: 'translateY(-2px)',
                boxShadow: 3 
              },
              transition: 'all 0.2s'
            }}
          >
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Projects
              </Typography>
              <Typography color="textSecondary" sx={{ flexGrow: 1, mb: 2 }}>
                Organize tasks into projects
              </Typography>
              <Button 
                variant="contained" 
                color="primary"
                fullWidth
                onClick={() => handleNavigation('/projects')}
              >
                View Projects
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card 
            sx={{ 
              height: '100%',
              '&:hover': { 
                transform: 'translateY(-2px)',
                boxShadow: 3 
              },
              transition: 'all 0.2s'
            }}
          >
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Integrations
              </Typography>
              <Typography color="textSecondary" sx={{ flexGrow: 1, mb: 2 }}>
                Connect external services and APIs
              </Typography>
              <Button 
                variant="contained" 
                color="primary"
                fullWidth
                onClick={() => handleNavigation('/integrations')}
              >
                View Integrations
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card 
            sx={{ 
              height: '100%',
              '&:hover': { 
                transform: 'translateY(-2px)',
                boxShadow: 3 
              },
              transition: 'all 0.2s'
            }}
          >
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Settings
              </Typography>
              <Typography color="textSecondary" sx={{ flexGrow: 1, mb: 2 }}>
                Configure your platform preferences
              </Typography>
              <Button 
                variant="contained" 
                color="primary"
                fullWidth
                onClick={() => handleNavigation('/settings')}
              >
                View Settings
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
