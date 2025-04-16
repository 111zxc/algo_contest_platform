import { Box, Button, Container, CssBaseline, Paper, TextField, Typography } from '@mui/material';
import axios from 'axios';
import React, { useContext, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import config from '../config';
import { AuthContext } from '../context/AuthContext';

export default function CreatePostPage() {
  const { auth } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();

  const searchParams = new URLSearchParams(location.search);
  const problem_id = searchParams.get('problem_id');

  const [formData, setFormData] = useState({
    problem_id: problem_id || '',
    language: 'russian',
    title: '',
    content: '',
  });
  const [error, setError] = useState('');

  useEffect(() => {
    if (!problem_id) {
      setError('Не указан идентификатор задачи');
    }
  }, [problem_id]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${config.GATEWAY_URL}/posts/`, formData, {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      navigate(-1);
    } catch (err) {
      setError('Ошибка создания поста');
    }
  };

  return (
    <Container component="main" sx={{ py: 4 }}>
      <CssBaseline />
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Создать пост
        </Typography>
        {error && <Typography color="error">{error}</Typography>}
        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="Название"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
          />
          <TextField
            label="Содержание"
            name="content"
            value={formData.content}
            onChange={handleChange}
            multiline
            rows={4}
            required
          />
          <Button variant="contained" type="submit">
            Создать пост
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}
