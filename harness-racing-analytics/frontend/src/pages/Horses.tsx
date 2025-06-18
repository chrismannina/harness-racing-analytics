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
import { Horse } from '../services/api';

const Horses: React.FC = () => {
  const [horses, setHorses] = useState<Horse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchHorses();
  }, []);

  const fetchHorses = async () => {
    try {
      setLoading(true);
      const response = await apiService.getHorses();
      setHorses(response);
    } catch (err) {
      setError('Failed to fetch horses');
      console.error('Error fetching horses:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredHorses = horses.filter(horse =>
    horse.name.toLowerCase().includes(searchTerm.toLowerCase())
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
        Horses
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          label="Search horses..."
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
        {filteredHorses.length === 0 ? (
          <Box sx={{ gridColumn: '1 / -1' }}>
            <Card>
              <CardContent>
                <Typography variant="h6" align="center" color="text.secondary">
                  No horses found
                </Typography>
              </CardContent>
            </Card>
          </Box>
        ) : (
          filteredHorses.map((horse) => (
            <Card
              key={horse.id}
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 4,
                },
              }}
              onClick={() => navigate(`/horses/${horse.id}`)}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h6" component="h2" gutterBottom>
                  {horse.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Sex: {horse.sex || 'Unknown'}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Registration: {horse.registration_number || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Owner: {horse.owner || 'Unknown'}
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color={horse.active ? 'success.main' : 'text.secondary'}>
                    Status: {horse.active ? 'Active' : 'Inactive'}
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

export default Horses;