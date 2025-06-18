import React from 'react';
import { Container, Typography, Card, CardContent } from '@mui/material';
import { useParams } from 'react-router-dom';

const RaceDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Race Detail - {id}
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="body1" color="text.secondary">
            Detailed race information will be displayed here.
          </Typography>
        </CardContent>
      </Card>
    </Container>
  );
};

export default RaceDetail;