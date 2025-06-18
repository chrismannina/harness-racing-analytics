import React from 'react';
import { Container, Typography, Card, CardContent } from '@mui/material';
import { useParams } from 'react-router-dom';

const TrainerDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Trainer Detail - {id}
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="body1" color="text.secondary">
            Detailed trainer information will be displayed here.
          </Typography>
        </CardContent>
      </Card>
    </Container>
  );
};

export default TrainerDetail;