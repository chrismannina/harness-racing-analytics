import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Box,
  Button,

  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import { Race, Track } from '../services/api';

const Races: React.FC = () => {
  const [races, setRaces] = useState<Race[]>([]);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());
  const [selectedTrack, setSelectedTrack] = useState<string>('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchRaces();
    fetchTracks();
  }, []);

  const fetchRaces = async () => {
    try {
      setLoading(true);
      const response = await apiService.getRaces();
      setRaces(response);
    } catch (err) {
      setError('Failed to fetch races');
      console.error('Error fetching races:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTracks = async () => {
    try {
      const response = await apiService.getTracks();
      setTracks(response);
    } catch (err) {
      console.error('Error fetching tracks:', err);
    }
  };

  const clearFilters = () => {
    setSelectedDate(new Date());
    setSelectedTrack('');
  };

  const formatDistance = (distance: number) => {
    return `${distance}m`;
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
    }).format(amount);
  };

  const filteredRaces = races.filter(race => {
    const matchesDate = !selectedDate || 
      new Date(race.race_date).toDateString() === selectedDate.toDateString();
    const matchesTrack = !selectedTrack || race.track.id.toString() === selectedTrack;
    return matchesDate && matchesTrack;
  });

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
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Races
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' },
              gap: 3,
              alignItems: 'center' 
            }}>
              <DatePicker
                label="Race Date"
                value={selectedDate}
                onChange={(newValue) => setSelectedDate(newValue)}
                slotProps={{ textField: { fullWidth: true } }}
              />
              <FormControl fullWidth>
                <InputLabel>Track</InputLabel>
                <Select
                  value={selectedTrack}
                  label="Track"
                  onChange={(e) => setSelectedTrack(e.target.value)}
                >
                  <MenuItem value="">All Tracks</MenuItem>
                  {tracks.map((track) => (
                    <MenuItem key={track.id} value={track.id.toString()}>
                      {track.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                variant="outlined"
                fullWidth
                onClick={clearFilters}
              >
                Clear Filters
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Race Results */}
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr', lg: '1fr 1fr 1fr' },
            gap: 3 
          }}>
            {filteredRaces.length === 0 ? (
              <Box sx={{ gridColumn: '1 / -1' }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" align="center" color="text.secondary">
                      No races found for the selected criteria
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            ) : (
              filteredRaces.map((race) => (
                <Card
                  key={race.id}
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    cursor: 'pointer',
                    '&:hover': {
                      boxShadow: 4,
                    },
                  }}
                  onClick={() => navigate(`/races/${race.id}`)}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" component="h2" gutterBottom>
                      Race {race.race_number}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {race.track.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {new Date(race.race_date).toLocaleDateString()} at {race.post_time}
                    </Typography>

                    <Box sx={{ mt: 2 }}>
                      <Box sx={{ 
                        display: 'grid', 
                        gridTemplateColumns: '1fr 1fr',
                        gap: 2 
                      }}>
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Distance
                          </Typography>
                          <Typography variant="body2" fontWeight="medium">
                            {race.distance ? formatDistance(race.distance) : 'N/A'}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Purse
                          </Typography>
                          <Typography variant="body2" fontWeight="medium">
                            {race.purse ? formatCurrency(race.purse) : 'N/A'}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>

                    {race.race_type && (
                      <Box sx={{ mt: 2 }}>
                        <Chip
                          label={race.race_type}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    )}

                    <Box sx={{ mt: 2 }}>
                      <Chip
                        label={race.status}
                        size="small"
                        color={race.status === 'finished' ? 'success' : 'primary'}
                      />
                    </Box>
                  </CardContent>
                </Card>
              ))
            )}
          </Box>
        )}
      </Container>
    </LocalizationProvider>
  );
};

export default Races;