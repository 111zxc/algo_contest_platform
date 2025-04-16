import {
  Box,
  Button,
  Container,
  CssBaseline,
  Paper,
  Typography
} from '@mui/material';
import axios from 'axios';
import React, { useContext, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import config from '../config';
import { AuthContext } from '../context/AuthContext';

export default function SolutionDetail() {
  const { solution_id } = useParams();
  const navigate = useNavigate();
  const { auth } = useContext(AuthContext);
  const [solution, setSolution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchSolution = async () => {
      try {
        const url = `${config.GATEWAY_URL}/solutions/${solution_id}`;
        const response = await axios.get(url, {
          headers: { Authorization: `Bearer ${auth.access_token}` },
        });
        setSolution(response.data);
      } catch (err) {
        setError('Ошибка загрузки решения.');
      } finally {
        setLoading(false);
      }
    };
    fetchSolution();
  }, [solution_id, auth.access_token]);

  if (loading) {
    return (
      <Container component="main" sx={{ py: 4 }}>
        <CssBaseline />
        <Typography variant="h6" align="center">
          Загрузка решения...
        </Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container component="main" sx={{ py: 4 }}>
        <CssBaseline />
        <Typography variant="h6" color="error" align="center">
          {error}
        </Typography>
        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <Button variant="outlined" onClick={() => navigate(-1)}>
            Назад
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container component="main" sx={{ py: 4 }}>
      <CssBaseline />
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Детали решения
        </Typography>
        <Typography variant="body1">
          <strong>Язык:</strong> {solution.language}
        </Typography>
        <Typography variant="body1">
          <strong>Статус:</strong> {solution.status}
        </Typography>
        <Typography variant="body1">
          <strong>Время выполнения:</strong> {solution.time_used} с
        </Typography>
        <Typography variant="body1">
          <strong>Быстрее чем:</strong> {solution.faster_than}%
        </Typography>
        <Typography variant="body1">
          <strong>Создано:</strong> {new Date(solution.created_at).toLocaleString()}
        </Typography>

        <Box sx={{ mt: 3 }}>
          <Typography variant="h6">Код решения</Typography>
          <Paper
            variant="outlined"
            sx={{
              p: 2,
              backgroundColor: '#f5f5f5',
              overflowX: 'auto',
            }}
          >
            <pre style={{ margin: 0 }}>{solution.code}</pre>
          </Paper>
        </Box>
        <Box sx={{ mt: 3, textAlign: 'right' }}>
          <Button variant="contained" onClick={() => navigate(-1)}>
            Назад
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}
