import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Container,
  CssBaseline,
  Paper,
  Snackbar,
  TextField,
  Typography
} from '@mui/material';
import axios from 'axios';
import React, { useContext, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import config from '../config';
import { AuthContext } from '../context/AuthContext';

export default function ProfilePage() {
  const { userId } = useParams();
  const { auth } = useContext(AuthContext);
  const navigate = useNavigate();

  const profileUserId = userId || auth.currentUser?.keycloak_id;

  const [profile, setProfile] = useState(null);
  const [posts, setPosts] = useState([]);
  const [problems, setProblems] = useState([]);
  const [comments, setComments] = useState([]);

  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadingPosts, setLoadingPosts] = useState(true);
  const [loadingProblems, setLoadingProblems] = useState(true);
  const [loadingComments, setLoadingComments] = useState(true);

  const [error, setError] = useState('');

  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({});

  const [notify, setNotify] = useState({
    open: false,
    severity: 'success',
    message: '',
  });

  const canEdit = (profileUserId === auth.currentUser?.keycloak_id) || auth.isAdmin;

  useEffect(() => {
    const fetchProfile = async () => {
      setLoadingProfile(true);
      try {
        const response = await axios.get(`${config.GATEWAY_URL}/users/${profileUserId}`, {
          headers: { Authorization: `Bearer ${auth.access_token}` },
        });
        setProfile(response.data);
        setEditData(response.data);
      } catch (err) {
        setError('Ошибка загрузки профиля.');
      } finally {
        setLoadingProfile(false);
      }
    };

    const fetchPosts = async () => {
      setLoadingPosts(true);
      try {
        const response = await axios.get(`${config.GATEWAY_URL}/posts/by-user/${profileUserId}`);
        setPosts(response.data);
      } catch (err) {
      } finally {
        setLoadingPosts(false);
      }
    };

    const fetchProblems = async () => {
      setLoadingProblems(true);
      try {
        const response = await axios.get(`${config.GATEWAY_URL}/problems/by-user/${profileUserId}`, {
          headers: { Authorization: `Bearer ${auth.access_token}` },
        });
        setProblems(response.data);
      } catch (err) {
      } finally {
        setLoadingProblems(false);
      }
    };

    const fetchComments = async () => {
      setLoadingComments(true);
      try {
        const response = await axios.get(`${config.GATEWAY_URL}/comments/user/${profileUserId}`);
        setComments(response.data);
      } catch (err) {
      } finally {
        setLoadingComments(false);
      }
    };

    if (profileUserId) {
      fetchProfile();
      fetchPosts();
      fetchProblems();
      fetchComments();
    }
  }, [profileUserId, auth.access_token]);

  const handleEditChange = (e) => {
    setEditData({ ...editData, [e.target.name]: e.target.value });
  };

  const handleSaveEdit = async () => {
    try {
      const response = await axios.put(`${config.GATEWAY_URL}/users/${profileUserId}`, editData, {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      setProfile(response.data);
      setIsEditing(false);
      setNotify({ open: true, severity: 'success', message: 'Профиль обновлен!' });
    } catch (err) {
      setNotify({ open: true, severity: 'error', message: 'Ошибка при обновлении профиля.' });
    }
  };

  const handleCancelEdit = () => {
    setEditData(profile);
    setIsEditing(false);
  };

  const handleDelete = async () => {
    if (window.confirm('Вы уверены, что хотите удалить пользователя?')) {
      try {
        await axios.delete(`${config.GATEWAY_URL}/users/${profileUserId}`, {
          headers: { Authorization: `Bearer ${auth.access_token}` },
        });
        setNotify({ open: true, severity: 'success', message: 'Пользователь удален.' });
        navigate('/');
      } catch (err) {
      }
    }
  };

  if (loadingProfile) {
    return (
      <Container sx={{ py: 4 }}>
        <CssBaseline />
        <CircularProgress />
      </Container>
    );
  }

  if (!profile) {
    return (
      <Container sx={{ py: 4 }}>
        <CssBaseline />
        <Typography color="error" align="center">
          Ошибка загрузки профиля.
        </Typography>
      </Container>
    );
  }

  return (
    <Container sx={{ py: 4 }}>
      <CssBaseline />
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Профиль пользователя
        </Typography>
        {isEditing ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Отображаемое имя"
              name="display_name"
              value={editData.display_name || ''}
              onChange={handleEditChange}
            />
            <TextField
              label="Имя"
              name="first_name"
              value={editData.first_name || ''}
              onChange={handleEditChange}
            />
            <TextField
              label="Фамилия"
              name="last_name"
              value={editData.last_name || ''}
              onChange={handleEditChange}
            />
            <TextField
              label="Username"
              name="username"
              value={editData.username || ''}
              onChange={handleEditChange}
            />
            <TextField
              label="Email"
              name="email"
              value={editData.email || ''}
              onChange={handleEditChange}
            />
            <Button variant="contained" onClick={handleSaveEdit}>
              Сохранить изменения
            </Button>
            <Button variant="outlined" onClick={handleCancelEdit}>
              Отмена
            </Button>
          </Box>
        ) : (
          <Box>
            <Typography variant="body1">
              <strong>Отображаемое имя:</strong> {profile.display_name}
            </Typography>
            <Typography variant="body1">
              <strong>Имя:</strong> {profile.first_name}
            </Typography>
            <Typography variant="body1">
              <strong>Фамилия:</strong> {profile.last_name}
            </Typography>
            <Typography variant="body1">
              <strong>Username:</strong> {profile.username}
            </Typography>
            <Typography variant="body1">
              <strong>Email:</strong> {profile.email}
            </Typography>
            <Typography variant="body1">
              <strong>Рейтинг:</strong> {profile.rating}
            </Typography>
            <Typography variant="body1">
              <strong>Создан:</strong> {new Date(profile.created_at).toLocaleString()}
            </Typography>
          </Box>
        )}
        {canEdit && !isEditing && (
          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button variant="contained" onClick={() => setIsEditing(true)}>
              Редактировать профиль
            </Button>
            {auth.isAdmin && (
              <Button variant="outlined" color="error" onClick={handleDelete}>
                Удалить пользователя
              </Button>
            )}
          </Box>
        )}
      </Paper>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Посты пользователя
        </Typography>
        {loadingPosts ? (
          <CircularProgress size={24} />
        ) : posts.length > 0 ? (
          posts.map((post) => (
            <Box
              key={post.id}
              component={Link}
              to={`/posts/${post.id}`}
              sx={{ mb: 2, textDecoration: 'none', color: 'inherit' }}
            >
              <Typography variant="subtitle1">{post.title}</Typography>
            </Box>
          ))
        ) : (
          <Typography variant="body2">Постов нет.</Typography>
        )}
      </Paper>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Задачи, созданные пользователем
        </Typography>
        {loadingProblems ? (
          <CircularProgress size={24} />
        ) : problems.length > 0 ? (
          problems.map((problem) => (
            <Box
              key={problem.id}
              component={Link}
              to={`/problems/${problem.id}`}
              sx={{ mb: 2, textDecoration: 'none', color: 'inherit' }}
            >
              <Typography variant="subtitle1">{problem.title}</Typography>
            </Box>
          ))
        ) : (
          <Typography variant="body2">Задач нет.</Typography>
        )}
      </Paper>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Комментарии пользователя
        </Typography>
        {loadingComments ? (
          <CircularProgress size={24} />
        ) : comments.length > 0 ? (
          comments.map((comment) => (
            <Box
              key={comment.id}
              component={Link}
              to={`/posts/${comment.post_id}`}
              sx={{ mb: 2, textDecoration: 'none', color: 'inherit' }}
            >
              <Typography variant="body2">{comment.content}</Typography>
              <Typography variant="caption" color="text.secondary">
                {new Date(comment.created_at).toLocaleString()}
              </Typography>
            </Box>
          ))
        ) : (
          <Typography variant="body2">Комментариев нет.</Typography>
        )}
      </Paper>

      <Snackbar
        open={notify.open}
        autoHideDuration={6000}
        onClose={() => setNotify({ ...notify, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity={notify.severity}
          onClose={() => setNotify({ ...notify, open: false })}
          sx={{ width: '100%' }}
        >
          {notify.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}
