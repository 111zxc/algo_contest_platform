import React, { useContext, useEffect, useState } from 'react';
import {
  Box,
  Button,
  CircularProgress,
  Container,
  CssBaseline,
  Paper,
  TextField,
  Typography
} from '@mui/material';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { AuthContext } from '../context/AuthContext';
import config from '../config';

export default function HomePage() {
  const { auth } = useContext(AuthContext);

  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [offset, setOffset] = useState(0);
  const limit = 10;

  // для inline‑редактирования
  const [editingId, setEditingId] = useState(null);
  const [editValues, setEditValues] = useState({ title: '', description: '' });

  const fetchPosts = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({ offset, limit });
      const resp = await axios.get(
        `${config.GATEWAY_URL}/blogposts?${params.toString()}`,
        {
          headers: auth.access_token
            ? { Authorization: `Bearer ${auth.access_token}` }
            : undefined,
        }
      );
      setPosts(resp.data);
    } catch (err) {
      console.error(err);
      setError('Не удалось загрузить блог‑посты.');
    } finally {
      setLoading(false);
      setEditingId(null);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, [offset]);

  const handleEditClick = (post) => {
    setEditingId(post.id);
    setEditValues({ title: post.title, description: post.description });
  };
  const handleCancel = () => {
    setEditingId(null);
  };
  const handleSave = async (id) => {
    try {
      await axios.put(
        `${config.GATEWAY_URL}/blogposts/${id}`,
        { title: editValues.title, description: editValues.description },
        { headers: { Authorization: `Bearer ${auth.access_token}` } }
      );
      await fetchPosts();
    } catch (err) {
      console.error(err);
      setError('Ошибка при сохранении.');
    }
  };

  const handleChange = (field) => (e) => {
    setEditValues((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handlePrev = () => {
    if (offset >= limit) setOffset(offset - limit);
  };
  const handleNext = () => {
    if (posts.length === limit) setOffset(offset + limit);
  };

  return (
    <Container component="main" sx={{ py: 8 }}>
      <CssBaseline />

      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography variant="h3" gutterBottom>
          Веб-приложение контестной системы
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Блог
        </Typography>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Typography color="error" align="center">
          {error}
        </Typography>
      ) : (
        <Box>
          {posts.map((post) => (
            <Paper key={post.id} sx={{ p: 2, mb: 2 }}>
              {editingId === post.id && auth.isAdmin ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    fullWidth
                    label="Заголовок"
                    value={editValues.title}
                    onChange={handleChange('title')}
                  />
                  <TextField
                    fullWidth
                    label="Описание (Markdown)"
                    multiline
                    minRows={4}
                    value={editValues.description}
                    onChange={handleChange('description')}
                  />
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={() => handleSave(post.id)}
                    >
                      Сохранить
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={handleCancel}
                    >
                      Отмена
                    </Button>
                  </Box>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h6">{post.title}</Typography>
                    <Box sx={{ mt: 1 }}>
                      <ReactMarkdown>{post.description}</ReactMarkdown>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Создано: {new Date(post.created_at).toLocaleString()}
                    </Typography>
                  </Box>
                  {auth.isAdmin && (
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => handleEditClick(post)}
                    >
                      Редактировать
                    </Button>
                  )}
                </Box>
              )}
            </Paper>
          ))}

          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mt: 4,
            }}
          >
            <Button
              variant="outlined"
              onClick={handlePrev}
              disabled={offset === 0}
            >
              Предыдущая
            </Button>
            <Typography>Страница {(offset / limit) + 1}</Typography>
            <Button
              variant="outlined"
              onClick={handleNext}
              disabled={posts.length < limit}
            >
              Следующая
            </Button>
          </Box>
        </Box>
      )}
    </Container>
  );
}
