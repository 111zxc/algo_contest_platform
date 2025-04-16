import { Box, Button, Paper, TextField, Typography } from '@mui/material';
import axios from 'axios';
import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

import config from '../config';

export default function LoginCard() {
  const navigate = useNavigate();
  const { setAuth } = useContext(AuthContext);
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  const handleChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const params = new URLSearchParams();
      params.append('grant_type', 'password');
      params.append('client_id', 'myclient');
      params.append('username', formData.username);
      params.append('password', formData.password);

      const loginResp = await axios.post(`${config.GATEWAY_URL}/login`, params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      localStorage.setItem('access_token', loginResp.data.access_token);
      localStorage.setItem('refresh_token', loginResp.data.refresh_token);

      const whoamiResp = await axios.get(`${config.GATEWAY_URL}/users/whoami`, {
        headers: {
          Authorization: `Bearer ${loginResp.data.access_token}`,
        },
      });

      const adminResp = await axios.get(`${config.GATEWAY_URL}/users/amiadmin`, {
        headers: {
          Authorization: `Bearer ${loginResp.data.access_token}`,
        },
      });
      localStorage.setItem('current_user', JSON.stringify(whoamiResp.data));

      setAuth({
        isAuthenticated: true,
        access_token: loginResp.data.access_token,
        refresh_token: loginResp.data.refresh_token,
        currentUser: whoamiResp.data,
        isAdmin: adminResp.data.is_admin,
      });

      navigate('/');
    } catch (err) {
      setError('Неверный логин или пароль.');
    }
  };

  return (
    <Paper elevation={6} sx={{ p: 4, width: 350, display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Typography variant="h5">Авторизация</Typography>
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
          label="Пароль"
          name="password"
          type="password"
          value={formData.password}
          onChange={handleChange}
          required
        />
        <Button type="submit" variant="contained">Войти</Button>
      </Box>
    </Paper>
  );
}
