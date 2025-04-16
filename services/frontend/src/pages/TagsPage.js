import CancelIcon from '@mui/icons-material/Cancel';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import {
  Box,
  Button,
  Container,
  IconButton, List, ListItem,
  ListItemSecondaryAction,
  ListItemText,
  Paper,
  TextField,
  Typography
} from '@mui/material';
import axios from 'axios';
import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import config from '../config';
import { AuthContext } from '../context/AuthContext';

export default function TagsPage() {
  const { auth } = useContext(AuthContext);
  const navigate = useNavigate();
  const [tags, setTags] = useState([]);
  const [error, setError] = useState('');
  const [newTagName, setNewTagName] = useState('');
  const [editingTagId, setEditingTagId] = useState(null);
  const [editingTagName, setEditingTagName] = useState('');

  useEffect(() => {
    if (!auth.isAdmin) {
      navigate('/');
    }
  }, [auth, navigate]);

  const fetchTags = async () => {
    try {
      const resp = await axios.get(`${config.GATEWAY_URL}/tags/`, {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      setTags(resp.data);
    } catch (err) {
      setError('Ошибка загрузки тегов.');
    }
  };

  useEffect(() => {
    fetchTags();
  }, []);

  const handleAddTag = async () => {
    if (!newTagName.trim()) return;
    try {
      const resp = await axios.post(`${config.GATEWAY_URL}/tags/`, { name: newTagName }, {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      setTags([...tags, resp.data]);
      setNewTagName('');
    } catch (err) {
      setError('Ошибка при добавлении тега.');
    }
  };

  const handleDeleteTag = async (id) => {
    try {
      await axios.delete(`${config.GATEWAY_URL}/tags/${id}`, {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      setTags(tags.filter(tag => tag.id !== id));
    } catch (err) {
      setError('Ошибка при удалении тега.');
    }
  };

  const startEditing = (tag) => {
    setEditingTagId(tag.id);
    setEditingTagName(tag.name);
  };

  const handleCancelEdit = () => {
    setEditingTagId(null);
    setEditingTagName('');
  };

  const handleSaveEdit = async (id) => {
    if (!editingTagName.trim()) return;
    try {
      const resp = await axios.put(`${config.GATEWAY_URL}/tags/${id}`, { name: editingTagName }, {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      setTags(tags.map(tag => tag.id === id ? resp.data : tag));
      setEditingTagId(null);
      setEditingTagName('');
    } catch (err) {
      setError('Ошибка при обновлении тега.');
    }
  };

  return (
    <Container component="main" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Управление Тегами
        </Typography>
        {error && <Typography color="error">{error}</Typography>}
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <TextField
            label="Новый тег"
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
          />
          <Button variant="contained" onClick={handleAddTag}>
            Добавить
          </Button>
        </Box>
        {tags.length === 0 ? (
          <Typography>Тегов нет.</Typography>
        ) : (
          <List>
            {tags.map((tag) => (
              <ListItem key={tag.id} sx={{ borderBottom: '1px solid', borderColor: 'divider' }}>
                {editingTagId === tag.id ? (
                  <>
                    <TextField
                      value={editingTagName}
                      onChange={(e) => setEditingTagName(e.target.value)}
                      size="small"
                    />
                    <ListItemSecondaryAction>
                      <IconButton edge="end" onClick={() => handleSaveEdit(tag.id)}>
                        <SaveIcon />
                      </IconButton>
                      <IconButton edge="end" onClick={handleCancelEdit}>
                        <CancelIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </>
                ) : (
                  <>
                    <ListItemText primary={tag.name} />
                    <ListItemSecondaryAction>
                      <IconButton edge="end" onClick={() => startEditing(tag)}>
                        <EditIcon />
                      </IconButton>
                      <IconButton edge="end" onClick={() => handleDeleteTag(tag.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </>
                )}
              </ListItem>
            ))}
          </List>
        )}
      </Paper>
    </Container>
  );
}
