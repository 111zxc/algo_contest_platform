import { Box, Button, Paper, TextField, Typography } from '@mui/material';
import axios from 'axios';
import * as React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import config from '../config';

export default function RegisterCard(props) {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    display_name: '',
    password: '',
    first_name: '',
    last_name: '',
  });
  const [error, setError] = useState('');

  const handleChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${config.GATEWAY_URL}/register/`, formData);
      navigate('/login');
    } catch (err) {
      setError('Ошибка регистрации. Проверьте вводимые данные.');
    }
  };

  return (
    <Paper elevation={6} sx={{ p: 4, width: 350, display: 'flex', flexDirection: 'column', gap: 2 }} {...props}>
      <Typography variant="h5">Регистрация</Typography>
      {error && <Typography color="error">{error}</Typography>}
      <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField
          label="Логин"
          name="username"
          value={formData.username}
          onChange={handleChange}
          required
        />
        <TextField
          label="Email"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleChange}
          required
        />
        <TextField
          label="Отображаемое имя"
          name="display_name"
          value={formData.display_name}
          onChange={handleChange}
        />
        <TextField
          label="Пароль"
          name="password"
          type="password"
          value={formData.password}
          onChange={handleChange}
          required
        />
        <TextField
          label="Имя"
          name="first_name"
          value={formData.first_name}
          onChange={handleChange}
        />
        <TextField
          label="Фамилия"
          name="last_name"
          value={formData.last_name}
          onChange={handleChange}
        />
        <Button type="submit" variant="contained">Зарегистрироваться</Button>
      </Box>
    </Paper>
  );
}
