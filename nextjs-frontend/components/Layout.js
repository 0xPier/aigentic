import { Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography, AppBar } from '@mui/material';
import { Home, Assignment, SmartToy, Folder, Settings, Power } from '@mui/icons-material';
import { useRouter } from 'next/router';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <Home />, path: '/' },
  { text: 'Tasks', icon: <Assignment />, path: '/tasks' },
  { text: 'Agents', icon: <SmartToy />, path: '/agents' },
  { text: 'Projects', icon: <Folder />, path: '/projects' },
  { text: 'Settings', icon: <Settings />, path: '/settings' },
  { text: 'Integrations', icon: <Power />, path: '/integrations' },
];

export default function Layout({ children }) {
  const router = useRouter();

  const handleNavigation = (path) => {
    console.log('Navigating to:', path);
    router.push(path);
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap component="div">
            AI Agent Platform
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton 
                  onClick={() => handleNavigation(item.path)}
                  selected={router.pathname === item.path}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: 'primary.light',
                      '&:hover': {
                        backgroundColor: 'primary.main',
                      },
                    },
                  }}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
