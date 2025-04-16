import { Box, Card, CardContent, Chip, Typography } from '@mui/material';
import React from 'react';

export default function ProblemCard({ problem }) {
  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {problem.title}
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 1 }}
        >
          {problem.description.length > 150
            ? problem.description.substring(0, 150) + '...'
            : problem.description}
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <Chip label={`Сложность: ${problem.difficulty}`} size="small" />
          <Typography variant="caption">
            Время: {problem.time_limit} с
          </Typography>
          <Typography variant="caption">
            Память: {problem.memory_limit} МБ
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}
