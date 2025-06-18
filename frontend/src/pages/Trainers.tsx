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
import { Trainer } from '../services/api';

const Trainers: React.FC = () => {
  const [trainers, setTrainers] = useState<Trainer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchTrainers();
  }, []);

  const fetchTrainers = async () => {
    try {
      setLoading(true);
      const response = await apiService.getTrainers();
      setTrainers(response);
    } catch (err) {
      setError('Failed to fetch trainers');
      console.error('Error fetching trainers:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredTrainers = trainers.filter(trainer =>
    trainer.name.toLowerCase().includes(searchTerm.toLowerCase())
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
        Trainers
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          label="Search trainers..."
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
        {filteredTrainers.length === 0 ? (
          <Box sx={{ gridColumn: '1 / -1' }}>
            <Card>
              <CardContent>
                <Typography variant="h6" align="center" color="text.secondary">
                  No trainers found
                </Typography>
              </CardContent>
            </Card>
          </Box>
        ) : (
          filteredTrainers.map((trainer) => (
            <Card
              key={trainer.id}
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 4,
                },
              }}
              onClick={() => navigate(`/trainers/${trainer.id}`)}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h6" component="h2" gutterBottom>
                  {trainer.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  License: {trainer.license_number || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Hometown: {trainer.hometown || 'Unknown'}
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color={trainer.active ? 'success.main' : 'text.secondary'}>
                    Status: {trainer.active ? 'Active' : 'Inactive'}
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

export default Trainers;