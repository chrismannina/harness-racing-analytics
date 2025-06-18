import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  DirectionsRun as RaceIcon,
  Pets as HorseIcon,
  Person as DriverIcon,
  School as TrainerIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { label: 'Dashboard', path: '/', icon: <DashboardIcon /> },
    { label: 'Races', path: '/races', icon: <RaceIcon /> },
    { label: 'Horses', path: '/horses', icon: <HorseIcon /> },
    { label: 'Drivers', path: '/drivers', icon: <DriverIcon /> },
    { label: 'Trainers', path: '/trainers', icon: <TrainerIcon /> },
    { label: 'Analytics', path: '/analytics', icon: <AnalyticsIcon /> },
  ];

  return (
    <AppBar position="static" elevation={2}>
      <Toolbar>
        <Typography
          variant="h6"
          component="div"
          sx={{ flexGrow: 1, fontWeight: 'bold', cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          🏇 Ontario Harness Racing Analytics
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          {menuItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              startIcon={item.icon}
              onClick={() => navigate(item.path)}
              sx={{
                backgroundColor: location.pathname === item.path ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;