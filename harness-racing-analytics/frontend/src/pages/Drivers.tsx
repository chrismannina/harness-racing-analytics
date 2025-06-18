import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Box,
  TextField,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import { Driver } from '../services/api';

const Drivers: React.FC = () => {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchDrivers();
  }, []);

  const fetchDrivers = async () => {
    try {
      setLoading(true);
      const response = await apiService.getDrivers();
      setDrivers(response);
    } catch (err) {
      setError('Failed to fetch drivers');
      console.error('Error fetching drivers:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredDrivers = drivers.filter(driver =>
    driver.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Drivers
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          label="Search drivers..."
          variant="outlined"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </Box>

      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' },
        gap: 3 
      }}>
        {filteredDrivers.length === 0 ? (
          <Box sx={{ gridColumn: '1 / -1' }}>
            <Card>
              <CardContent>
                <Typography variant="h6" align="center" color="text.secondary">
                  No drivers found
                </Typography>
              </CardContent>
            </Card>
          </Box>
        ) : (
          filteredDrivers.map((driver) => (
            <Card
              key={driver.id}
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 4,
                },
              }}
              onClick={() => navigate(`/drivers/${driver.id}`)}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h6" component="h2" gutterBottom>
                  {driver.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  License: {driver.license_number || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Hometown: {driver.hometown || 'Unknown'}
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color={driver.active ? 'success.main' : 'text.secondary'}>
                    Status: {driver.active ? 'Active' : 'Inactive'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          ))
        )}
      </Box>
    </Container>
  );
};

export default Drivers;