import { Box, Container, CssBaseline, Typography } from '@mui/material';
import * as React from 'react';

export default function HomePage() {
  return (
    <Container component="main" sx={{ py: 8, textAlign: 'center' }}>
      <CssBaseline />
      <Box>
        <Typography variant="h3" gutterBottom>
          Lorem Ipsum Dolor
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Lorem Ipsum DolorLorem Ipsum DolorLorem Ipsum Dolor
        </Typography>
      </Box>
    </Container>
  );
}
