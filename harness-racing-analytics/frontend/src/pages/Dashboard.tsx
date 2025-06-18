import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Box,
  Button,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import {
  DirectionsRun as RaceIcon,
  Pets as HorseIcon,
  Person as DriverIcon,
  School as TrainerIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { apiService, DashboardData } from '../services/api';
import { format } from 'date-fns';

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadDashboardData = async () => {
    try {
      setError(null);
      const data = await apiService.getDashboardData();
      setDashboardData(data);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshData = async () => {
    setRefreshing(true);
    try {
      await apiService.fetchLatestData();
      await loadDashboardData();
    } catch (err) {
      setError('Failed to refresh data');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  const StatCard: React.FC<{ title: string; value: number; icon: React.ReactNode; color: string }> = ({
    title,
    value,
    icon,
    color,
  }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box sx={{ color, mr: 2 }}>{icon}</Box>
          <Typography variant="h6" component="div">
            {title}
          </Typography>
        </Box>
        <Typography variant="h3" component="div" sx={{ fontWeight: 'bold', color }}>
          {value.toLocaleString()}
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Button
          variant="contained"
          startIcon={refreshing ? <CircularProgress size={20} /> : <RefreshIcon />}
          onClick={handleRefreshData}
          disabled={refreshing}
        >
          {refreshing ? 'Refreshing...' : 'Refresh Data'}
        </Button>
      </Box>

      {/* Statistics Cards */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' },
        gap: 3,
        mb: 4 
      }}>
        <StatCard
          title="Races Today"
          value={dashboardData?.total_races_today || 0}
          icon={<RaceIcon fontSize="large" />}
          color="#1976d2"
        />
        <StatCard
          title="Active Horses"
          value={dashboardData?.total_horses || 0}
          icon={<HorseIcon fontSize="large" />}
          color="#2e7d32"
        />
        <StatCard
          title="Active Drivers"
          value={dashboardData?.total_drivers || 0}
          icon={<DriverIcon fontSize="large" />}
          color="#ed6c02"
        />
        <StatCard
          title="Active Trainers"
          value={dashboardData?.total_trainers || 0}
          icon={<TrainerIcon fontSize="large" />}
          color="#9c27b0"
        />
      </Box>

      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
        gap: 3 
      }}>
        {/* Recent Races */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Races
            </Typography>
            {dashboardData?.recent_races?.length ? (
              <Box>
                {dashboardData.recent_races.slice(0, 5).map((race) => (
                  <Box
                    key={race.id}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      py: 1,
                      borderBottom: '1px solid #eee',
                      '&:last-child': { borderBottom: 'none' },
                    }}
                  >
                    <Box>
                      <Typography variant="body1" fontWeight="medium">
                        Race {race.race_number} - {race.track.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {format(new Date(race.race_date), 'MMM dd, yyyy')}
                      </Typography>
                    </Box>
                    <Chip
                      label={race.status}
                      color={race.status === 'finished' ? 'success' : 'primary'}
                      size="small"
                    />
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography color="text.secondary">No recent races found</Typography>
            )}
          </CardContent>
        </Card>

        {/* Top Horses */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Top Horses (by Wins)
            </Typography>
            {dashboardData?.top_horses?.length ? (
              <Box>
                {dashboardData.top_horses.slice(0, 5).map((horse, index) => (
                  <Box
                    key={horse.id}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      py: 1,
                      borderBottom: '1px solid #eee',
                      '&:last-child': { borderBottom: 'none' },
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography
                        variant="body2"
                        sx={{
                          minWidth: 24,
                          height: 24,
                          borderRadius: '50%',
                          backgroundColor: '#1976d2',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mr: 2,
                          fontSize: '0.75rem',
                        }}
                      >
                        {index + 1}
                      </Typography>
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {horse.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {horse.win_percentage}% win rate
                        </Typography>
                      </Box>
                    </Box>
                    <Typography variant="body1" fontWeight="bold" color="primary">
                      {horse.wins} wins
                    </Typography>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography color="text.secondary">No horse data available</Typography>
            )}
          </CardContent>
        </Card>

        {/* Top Drivers */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Top Drivers (by Wins)
            </Typography>
            {dashboardData?.top_drivers?.length ? (
              <Box>
                {dashboardData.top_drivers.slice(0, 5).map((driver, index) => (
                  <Box
                    key={driver.id}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      py: 1,
                      borderBottom: '1px solid #eee',
                      '&:last-child': { borderBottom: 'none' },
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography
                        variant="body2"
                        sx={{
                          minWidth: 24,
                          height: 24,
                          borderRadius: '50%',
                          backgroundColor: '#ed6c02',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mr: 2,
                          fontSize: '0.75rem',
                        }}
                      >
                        {index + 1}
                      </Typography>
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {driver.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {driver.win_percentage}% win rate
                        </Typography>
                      </Box>
                    </Box>
                    <Typography variant="body1" fontWeight="bold" color="primary">
                      {driver.wins} wins
                    </Typography>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography color="text.secondary">No driver data available</Typography>
            )}
          </CardContent>
        </Card>

        {/* Top Trainers */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Top Trainers (by Wins)
            </Typography>
            {dashboardData?.top_trainers?.length ? (
              <Box>
                {dashboardData.top_trainers.slice(0, 5).map((trainer, index) => (
                  <Box
                    key={trainer.id}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      py: 1,
                      borderBottom: '1px solid #eee',
                      '&:last-child': { borderBottom: 'none' },
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography
                        variant="body2"
                        sx={{
                          minWidth: 24,
                          height: 24,
                          borderRadius: '50%',
                          backgroundColor: '#9c27b0',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mr: 2,
                          fontSize: '0.75rem',
                        }}
                      >
                        {index + 1}
                      </Typography>
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {trainer.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {trainer.win_percentage}% win rate
                        </Typography>
                      </Box>
                    </Box>
                    <Typography variant="body1" fontWeight="bold" color="primary">
                      {trainer.wins} wins
                    </Typography>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography color="text.secondary">No trainer data available</Typography>
            )}
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};

export default Dashboard;