import CancelIcon from '@mui/icons-material/Cancel';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import {
  Box,
  Button,
  Chip,
  Container,
  CssBaseline,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  TextField,
  Typography
} from '@mui/material';
import { grey } from '@mui/material/colors';
import axios from 'axios';
import AceEditor from 'react-ace';
import React, { useContext, useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Link, useNavigate, useParams } from 'react-router-dom';
import config from '../config';
import { AuthContext } from '../context/AuthContext';

import 'ace-builds/src-noconflict/mode-c_cpp';
import 'ace-builds/src-noconflict/mode-java';
import 'ace-builds/src-noconflict/mode-javascript';
import 'ace-builds/src-noconflict/mode-python';
import 'ace-builds/src-noconflict/theme-github';


const CommentItem = ({ comment, level = 0, postAuthorId, refreshComments }) => {
  const { auth } = useContext(AuthContext);
  const [replying, setReplying] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(comment.content);
  const [localReaction, setLocalReaction] = useState(comment.user_reaction);

  useEffect(() => {
    setLocalReaction(comment.user_reaction);
  }, [comment.id, comment.user_reaction]);



  const handleReplySubmit = async () => {
    if (!replyContent.trim()) return;
    try {
      await axios.post(
        `${config.GATEWAY_URL}/comments/`,
        {
          content: replyContent,
          post_id: comment.post_id,
          parent_comment_id: comment.id,
        },
        { headers: { Authorization: `Bearer ${auth.access_token}` } }
      );
      setReplyContent('');
      setReplying(false);
      if (refreshComments) refreshComments();
    } catch (err) {
    }
  };

  const handleEditSubmit = async () => {
    if (!editedContent.trim()) return;
    try {
      await axios.put(
        `${config.GATEWAY_URL}/comments/${comment.id}`,
        { content: editedContent },
        { headers: { Authorization: `Bearer ${auth.access_token}` } }
      );
      setIsEditing(false);
      if (refreshComments) refreshComments();
    } catch (err) {
    }
  };

  const handleCommentReaction = async (reactionType) => {
    try {
      await axios.post(
        `${config.GATEWAY_URL}/reactions/`,
        {
          target_id: comment.id,
          target_type: 'comment',
          reaction_type: reactionType,
        },
        { headers: { Authorization: `Bearer ${auth.access_token}` } }
      );
      setLocalReaction((prev) => (prev === reactionType ? null : reactionType));
      if (refreshComments) refreshComments();
    } catch (err) {
    }
  };

  const isPostAuthor = comment.created_by === postAuthorId;

  return (
    <Box sx={{ ml: level * 3, mt: 1 }}>
      <Paper variant="outlined" sx={{ p: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          {isPostAuthor ? (
            <Chip
              label={
                <Link to={`/profile/${comment.created_by}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                  {comment.author_display_name || comment.created_by}
                </Link>
              }
              size="small"
              variant="outlined"
              sx={{ backgroundColor: grey[200], color: 'black' }}
            />
          ) : (
            <Typography
              variant="caption"
              component={Link}
              to={`/profile/${comment.created_by}`}
              sx={{ textDecoration: 'none', color: 'inherit' }}
            >
              {comment.author_display_name || comment.created_by}
            </Typography>
          )}
          <Typography variant="caption" color="text.secondary">
            {new Date(comment.created_at).toLocaleString()}
          </Typography>
        </Box>

        {isEditing ? (
          <Box sx={{ my: 1 }}>
            <TextField
              fullWidth
              multiline
              size="small"
              variant="outlined"
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
            />
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Button size="small" variant="contained" onClick={handleEditSubmit}>
                Save
              </Button>
              <Button
                size="small"
                variant="outlined"
                onClick={() => {
                  setIsEditing(false);
                  setEditedContent(comment.content);
                }}
              >
                Cancel
              </Button>
            </Box>
          </Box>
        ) : (
          <ReactMarkdown>{comment.content}</ReactMarkdown>
        )}

        {comment.updated_at && (
          <Typography variant="caption" color="grey" sx={{ display: 'block', mt: 0.5 }}>
            Обновлено: {new Date(comment.updated_at).toLocaleString()}
          </Typography>
        )}

        <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            label={`${comment.reaction_balance > 0 ? `+${comment.reaction_balance}` : comment.reaction_balance}`}
            size="small"
            color={comment.reaction_balance > 0 ? 'success' : (comment.reaction_balance < 0 ? 'error' : 'warning')}
          />
          <Button
            variant={localReaction === 'plus' ? 'contained' : 'outlined'}
            color="success"
            size="small"
            onClick={() => handleCommentReaction('plus')}
          >
            +
          </Button>
          <Button
            variant={localReaction === 'minus' ? 'contained' : 'outlined'}
            color="error"
            size="small"
            onClick={() => handleCommentReaction('minus')}
          >
            –
          </Button>
        </Box>

        <Box sx={{ mt: 1 }}>
          {comment.created_by === auth.currentUser?.keycloak_id && (
            <Button size="small" onClick={() => setIsEditing(true)}>
              Редактировать
            </Button>
          )}
          <Button size="small" onClick={() => setReplying(!replying)}>
            Ответить
          </Button>
        </Box>

        {replying && (
          <Box sx={{ mt: 1 }}>
            <TextField
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              fullWidth
              multiline
              rows={2}
              variant="outlined"
              label="Ваш ответ"
            />
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mt: 1 }}>
              <Button size="small" variant="outlined" onClick={() => setReplying(false)}>
                Cancel
              </Button>
              <Button size="small" variant="contained" onClick={handleReplySubmit}>
                Submit
              </Button>
            </Box>
          </Box>
        )}
      </Paper>
      {comment.children && comment.children.length > 0 && (
        <Box>
          {comment.children.map((child) => (
            <CommentItem
              key={child.id}
              comment={child}
              level={level + 1}
              postAuthorId={postAuthorId}
              refreshComments={refreshComments}
            />
          ))}
        </Box>
      )}
    </Box>
  );
};

const buildCommentTree = (commentsList) => {
  const lookup = {};
  const tree = [];
  commentsList.forEach((comment) => {
    lookup[comment.id] = { ...comment, children: [] };
  });
  commentsList.forEach((comment) => {
    if (comment.parent_comment_id && lookup[comment.parent_comment_id]) {
      lookup[comment.parent_comment_id].children.push(lookup[comment.id]);
    } else {
      tree.push(lookup[comment.id]);
    }
  });
  return tree;
};

export default function PostDetail() {
  const { postId } = useParams();
  const navigate = useNavigate();
  const { auth } = useContext(AuthContext);

  const [post, setPost] = useState(null);
  const [authorDisplayName, setAuthorDisplayName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({});

  const [availableTags, setAvailableTags] = useState([]);
  const [selectedTagToAttach, setSelectedTagToAttach] = useState('');

  const [comments, setComments] = useState([]);
  const [commentTree, setCommentTree] = useState([]);
  const [commentOffset, setCommentOffset] = useState(0);
  const commentLimit = 10;
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [commentsError, setCommentsError] = useState('');
  const [newCommentContent, setNewCommentContent] = useState('');

  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState('');

  const goBack = () => navigate(-1);

  const refreshComments = async () => {
    try {
      const resp = await axios.get(
        `${config.GATEWAY_URL}/comments/post/enriched/${postId}?offset=0&limit=${commentLimit}`,
        { headers: { Authorization: `Bearer ${auth.access_token}` } }
      );
      setComments(resp.data);
      setCommentOffset(0);
    } catch (err) {
      setCommentsError('Ошибка загрузки комментариев.');
    }
  };

  useEffect(() => {
    const fetchPost = async () => {
      try {
        const url = auth.currentUser
          ? `${config.GATEWAY_URL}/posts/${postId}?current_user_id=${auth.currentUser.keycloak_id}`
          : `${config.GATEWAY_URL}/posts/${postId}`;
        const resp = await axios.get(url, {
          headers: { Authorization: `Bearer ${auth.access_token}` },
        });
        setPost(resp.data);
        setEditData({
          title: resp.data.title,
          content: resp.data.content,
          language: resp.data.language,
          tags: resp.data.tags || [],
        });
        const authorResp = await axios.get(
          `${config.GATEWAY_URL}/users/${resp.data.created_by}`,
          { headers: { Authorization: `Bearer ${auth.access_token}` } }
        );
        setAuthorDisplayName(authorResp.data.display_name);
      } catch (err) {
        setError('Ошибка загрузки поста.');
      } finally {
        setLoading(false);
      }
    };
    fetchPost();
  }, [postId, auth.access_token]);

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const resp = await axios.get(`${config.GATEWAY_URL}/tags/`, {
          headers: { Authorization: `Bearer ${auth.access_token}` },
        });
        setAvailableTags(resp.data);
      } catch (err) {
      }
    };
    fetchTags();
  }, [auth.access_token]);

  useEffect(() => {
    const fetchComments = async () => {
      setCommentsLoading(true);
      try {
        if (auth.currentUser) {
          var url = `${config.GATEWAY_URL}/comments/post/enriched/${postId}?offset=${commentOffset}&limit=${commentLimit}&current_user_id=${auth.currentUser.keycloak_id}`
        }
        else {
          var url = `${config.GATEWAY_URL}/comments/post/enriched/${postId}?offset=${commentOffset}&limit=${commentLimit}`
        }
        const resp = await axios.get(
          url,
          { headers: { Authorization: `Bearer ${auth.access_token}` } }
        );
        setComments(resp.data);
      } catch (err) {
        setCommentsError('Ошибка загрузки комментариев.');
      } finally {
        setCommentsLoading(false);
      }
    };
    fetchComments();
  }, [postId, commentOffset, auth.access_token]);

  useEffect(() => {
    setCommentTree(buildCommentTree(comments));
  }, [comments]);

  const handleCommentPrev = () => {
    if (commentOffset >= commentLimit) {
      setCommentOffset(commentOffset - commentLimit);
    }
  };

  const handleCommentNext = () => {
    if (comments.length === commentLimit) {
      setCommentOffset(commentOffset + commentLimit);
    }
  };

  const handleSubmitComment = async () => {
    if (!newCommentContent.trim()) return;
    try {
      await axios.post(
        `${config.GATEWAY_URL}/comments/`,
        {
          content: newCommentContent,
          post_id: post.id,
          parent_comment_id: null,
        },
        { headers: { Authorization: `Bearer ${auth.access_token}` } }
      );
      setNewCommentContent('');
      await refreshComments();
    } catch (err) {
      setCommentsError('Ошибка при добавлении комментария.');
    }
  };

  const canEdit = post && (post.created_by === auth.currentUser?.keycloak_id || auth.isAdmin);

  const handleEditChange = (e) => {
    setEditData({ ...editData, [e.target.name]: e.target.value });
  };

  const handleDelete = async () => {
    if (window.confirm('Вы уверены, что хотите удалить этот пост?')) {
      try {
        await axios.delete(`${config.GATEWAY_URL}/posts/${post.id}`, {
          headers: { Authorization: `Bearer ${auth.access_token}` },
        });
        navigate(-1);
      } catch (err) {
        setError('Ошибка при удалении поста.');
      }
    }
  };


  const handleReaction = async (reactionType) => {
    try {
      await axios.post(
        `${config.GATEWAY_URL}/reactions/`,
        {
          target_id: post.id,
          target_type: "post",
          reaction_type: reactionType,
        },
        { headers: { Authorization: `Bearer ${auth.access_token}` } }
      );
      const url = auth.currentUser
        ? `${config.GATEWAY_URL}/posts/${postId}?current_user_id=${auth.currentUser.keycloak_id}`
        : `${config.GATEWAY_URL}/posts/${postId}`;
      const resp = await axios.get(url, { headers: { Authorization: `Bearer ${auth.access_token}` } });
      setPost(resp.data);
    } catch (err) {
    }
  };

  const handleSaveEdit = async () => {
    try {
      const resp = await axios.put(`${config.GATEWAY_URL}/posts/${post.id}`, editData, {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      setPost(resp.data);
      setIsEditing(false);
    } catch (err) {
      setError('Ошибка обновления поста.');
    }
  };

  const handleCancelEdit = () => {
    setEditData({
      title: post.title,
      content: post.content,
      language: post.language,
      tags: post.tags || [],
    });
    setIsEditing(false);
  };

  const handleAttachTag = async () => {
    if (!selectedTagToAttach) return;
    try {
      await axios.post(
        `${config.GATEWAY_URL}/posts/${post.id}/tags/${selectedTagToAttach}`,
        {},
        { headers: { Authorization: `Bearer ${auth.access_token}` } }
      );
      const tagToAdd = availableTags.find((tag) => tag.id === selectedTagToAttach);
      if (tagToAdd && !post.tags.some((t) => t.id === tagToAdd.id)) {
        setPost({ ...post, tags: [...post.tags, tagToAdd] });
      }
      setSelectedTagToAttach('');
    } catch (err) {
      setError('Ошибка при прикреплении тега.');
    }
  };

  const handleDetachTag = async (tagId) => {
    try {
      await axios.delete(`${config.GATEWAY_URL}/posts/${post.id}/tags/${tagId}`, {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      const newTags = post.tags.filter((tag) => tag.id !== tagId);
      setPost({ ...post, tags: newTags });
    } catch (err) {
      setError('Ошибка при откреплении тега.');
    }
  };


  const handleLanguageChange = (e) => {
    setLanguage(e.target.value);
  };

  if (loading) {
    return (
      <Container component="main" sx={{ py: 8 }}>
        <CssBaseline />
        <Typography variant="h6" align="center">
          Загрузка поста...
        </Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container component="main" sx={{ py: 8 }}>
        <CssBaseline />
        <Typography variant="h6" color="error" align="center">
          {error}
        </Typography>
      </Container>
    );
  }

  if (!post) {
    return (
      <Container component="main" sx={{ py: 8 }}>
        <CssBaseline />
        <Typography variant="h6" align="center">
          Пост не найден.
        </Typography>
      </Container>
    );
  }

  return (
    <Container component="main" sx={{ py: 4 }}>
      <CssBaseline />
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        {isEditing ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Название"
              name="title"
              value={editData.title}
              onChange={handleEditChange}
              required
            />
            <TextField
              label="Содержание"
              name="content"
              value={editData.content}
              onChange={handleEditChange}
              multiline
              rows={4}
              required
            />
            <FormControl fullWidth>
              <InputLabel id="language-select-label">Язык</InputLabel>
              <Select
                labelId="language-select-label"
                name="language"
                value={editData.language}
                label="Язык"
                onChange={handleEditChange}
              >
                <MenuItem value="russian">Russian</MenuItem>
                <MenuItem value="python">Python</MenuItem>
                <MenuItem value="java">Java</MenuItem>
                <MenuItem value="javascript">JavaScript</MenuItem>
                <MenuItem value="c_cpp">C++</MenuItem>
              </Select>
            </FormControl>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="contained" onClick={handleSaveEdit} startIcon={<SaveIcon />}>
                Сохранить
              </Button>
              <Button variant="outlined" onClick={handleCancelEdit} startIcon={<CancelIcon />}>
                Отмена
              </Button>
            </Box>
          </Box>
        ) : (
          <Box>
            <Typography variant="h4" gutterBottom>
              {post.title}
            </Typography>
            <Typography variant="subtitle1" gutterBottom>
              Автор:{' '}
              <Link to={`/profile/${post.created_by}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                {authorDisplayName}
              </Link>
            </Typography>
            <ReactMarkdown>{post.content}</ReactMarkdown>
            <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 2 }}>
              <Chip
                label={`${post.reaction_balance > 0 ? `+${post.reaction_balance}` : post.reaction_balance}`}
                size="small"
                color={post.reaction_balance > 0 ? 'success' : (post.reaction_balance < 0 ? 'error' : 'warning')}
              />
              <Button
                variant={post.user_reaction === 'plus' ? 'contained' : 'outlined'}
                color="success"
                size="small"
                onClick={() => handleReaction('plus')}
              >
                +
              </Button>
              <Button
                variant={post.user_reaction === 'minus' ? 'contained' : 'outlined'}
                color="error"
                size="small"
                onClick={() => handleReaction('minus')}
              >
                –
              </Button>
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Создано: {new Date(post.created_at).toLocaleString()}
              </Typography>
              {post.updated_at && (
                <Typography variant="caption" color="text.secondary">
                  Обновлено: {new Date(post.updated_at).toLocaleString()}
                </Typography>
              )}
            </Box>
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6">Теги</Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
                {post.tags && post.tags.map((tag) => (
                  <Chip
                    key={tag.id}
                    label={tag.name}
                    size="small"
                    variant="outlined"
                    onDelete={canEdit ? () => handleDetachTag(tag.id) : undefined}
                  />
                ))}
              </Box>
              {canEdit && (
                <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                  <FormControl sx={{ minWidth: 150 }}>
                    <InputLabel id="post-attach-tag-label">Прикрепить тег</InputLabel>
                    <Select
                      labelId="post-attach-tag-label"
                      value={selectedTagToAttach}
                      label="Прикрепить тег"
                      onChange={(e) => setSelectedTagToAttach(e.target.value)}
                    >
                      <MenuItem value="">
                        <em>Выберите тег</em>
                      </MenuItem>
                      {availableTags
                        .filter(tag => !post.tags.some(t => t.id === tag.id))
                        .map(tag => (
                          <MenuItem key={tag.id} value={tag.id}>
                            {tag.name}
                          </MenuItem>
                        ))}
                    </Select>
                  </FormControl>
                  <Button variant="contained" onClick={handleAttachTag}>
                    Прикрепить
                  </Button>
                </Box>
              )}
            </Box>

          </Box>
        )}
      </Paper>

      {canEdit && !isEditing && (
        <Box sx={{ mb: 4, display: 'flex', gap: 2 }}>
          <Button variant="contained" onClick={() => setIsEditing(true)} startIcon={<EditIcon />}>
            Редактировать
          </Button>
          <Button variant="outlined" color="error" onClick={handleDelete}>
            Удалить
          </Button>
        </Box>
      )}

      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>
          Комментарии
        </Typography>

        <Box sx={{ mb: 2 }}>
          <TextField
            label="Новый комментарий"
            value={newCommentContent}
            onChange={(e) => setNewCommentContent(e.target.value)}
            fullWidth
            multiline
            rows={3}
            variant="outlined"
          />
          <Box sx={{ textAlign: 'right', mt: 1 }}>
            <Button variant="contained" onClick={handleSubmitComment}>
              Отправить
            </Button>
          </Box>
        </Box>

        {commentsLoading ? (
          <Typography>Загрузка комментариев...</Typography>
        ) : commentsError ? (
          <Typography color="error">{commentsError}</Typography>
        ) : (
          <>
            {commentTree.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                postAuthorId={post.created_by}
                refreshComments={refreshComments}
              />
            ))}
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mt: 2,
              }}
            >
              <Button variant="outlined" onClick={handleCommentPrev} disabled={commentOffset === 0}>
                Предыдущая
              </Button>
              <Typography variant="body2">
                Страница {(commentOffset / commentLimit) + 1}
              </Typography>
              <Button variant="outlined" onClick={handleCommentNext} disabled={comments.length < commentLimit}>
                Следующая
              </Button>
            </Box>
          </>
        )}
      </Box>
    </Container>
  );
}
