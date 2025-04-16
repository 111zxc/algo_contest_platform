import {
  Box,
  Button,
  Chip,
  Container,
  CssBaseline,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import React, { useContext, useEffect, useState } from 'react';

import DeleteIcon from '@mui/icons-material/Delete';
import { grey } from '@mui/material/colors';
import axios from 'axios';
import AceEditor from 'react-ace';
import { useNavigate, useParams } from 'react-router-dom';
import config from '../config';
import { AuthContext } from '../context/AuthContext';

import ReactMarkdown from 'react-markdown';

import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import { Tooltip } from '@mui/material';

import 'ace-builds/src-noconflict/mode-c_cpp';
import 'ace-builds/src-noconflict/mode-java';
import 'ace-builds/src-noconflict/mode-javascript';
import 'ace-builds/src-noconflict/mode-python';
import 'ace-builds/src-noconflict/theme-github';

import { Link } from 'react-router-dom';

const difficultyColorMapping = {
  EASY: 'success',
  MEDIUM: 'warning',
  HARD: 'error',
};

const formatReactionBalance = (balance) =>
  balance > 0 ? `+${balance}` : `${balance}`;
const getReactionColor = (balance) => {
  if (balance > 0) return "success";
  if (balance < 0) return "error";
  return "warning";
};

export default function ProblemDetail() {
  const [postTagFilter, setPostTagFilter] = useState('');
  const { problemId } = useParams();
  const navigate = useNavigate();
  const { auth } = useContext(AuthContext);

  const [problem, setProblem] = useState(null);
  const [author, setAuthor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [notify, setNotify] = useState({
    open: false,
    severity: 'success',
    message: '',
  });


  const [sortPostsByRating, setSortPostsByRating] = useState(false);
  const [sortPostsOrder, setSortPostsOrder] = useState('desc');


  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({});


  const [showMySolutions, setShowMySolutions] = useState(false);
  const [mySolutions, setMySolutions] = useState([]);
  const [solutionsLoading, setSolutionsLoading] = useState(false);
  const [solutionsError, setSolutionsError] = useState('');

  const [availableTags, setAvailableTags] = useState([]);
  const [selectedTagToAttach, setSelectedTagToAttach] = useState('');

  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState('');

  const [posts, setPosts] = useState([]);
  const [postOffset, setPostOffset] = useState(0);
  const postLimit = 10;
  const [postsLoading, setPostsLoading] = useState(false);
  const [postsError, setPostsError] = useState('');

  const handleSubmitSolution = async () => {
    try {
      const payload = {
        problem_id: problem.id,
        code: code,
        language: language,
      };
      const resp = await axios.post(`${config.GATEWAY_URL}/solutions/`, payload, {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      setNotify({
        open: true,
        severity: 'success',
        message: 'Решение успешно отправлено!',
      });
    } catch (err) {
      setNotify({
        open: true,
        severity: 'error',
        message: 'Ошибка при отправке решения!',
      });
    }
  };


  const fetchMySolutions = async () => {
    setSolutionsLoading(true);
    try {
      const resp = await axios.get(
        `${config.GATEWAY_URL}/solutions/my/${problem.id}`,
        { headers: { Authorization: `Bearer ${auth.access_token}` } }
      );
      setMySolutions(resp.data);
      setSolutionsError('');
    } catch (err) {
      setSolutionsError('Ошибка загрузки решений.');
    } finally {
      setSolutionsLoading(false);
    }
  };


  const navigateToProblems = () => navigate('/problems');

  const canEdit =
    problem &&
    (problem.created_by === auth.currentUser?.keycloak_id || auth.isAdmin);



  useEffect(() => {
    if (showMySolutions) {
      fetchMySolutions();
    }
  }, [showMySolutions, problem?.id, auth.access_token]);

  useEffect(() => {
    const fetchProblem = async () => {
      try {
        const url = auth.currentUser
          ? `${config.GATEWAY_URL}/problems/${problemId}?user_id=${auth.currentUser.keycloak_id}`
          : `${config.GATEWAY_URL}/problems/${problemId}`;
        const resp = await axios.get(url, {
          headers: { Authorization: `Bearer ${auth.access_token}` },
        });
        setProblem(resp.data);
        setEditData({
          title: resp.data.title,
          description: resp.data.description,
          difficulty: resp.data.difficulty,
          time_limit: resp.data.time_limit,
          memory_limit: resp.data.memory_limit,
          test_cases: resp.data.test_cases,
          tags: resp.data.tags || [],
        });
        const respAuthor = await axios.get(
          `${config.GATEWAY_URL}/users/${resp.data.created_by}`,
          { headers: { Authorization: `Bearer ${auth.access_token}` } }
        );
        setAuthor(respAuthor.data);
      } catch (err) {
        setError('Ошибка загрузки задачи.');
      } finally {
        setLoading(false);
      }
    };
    fetchProblem();
  }, [problemId, auth.access_token]);

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
    const fetchPosts = async () => {
      if (!problem?.id) return;
      setPostsLoading(true);
      try {
        const params = new URLSearchParams();
        params.append('offset', postOffset);
        params.append('limit', postLimit);
        const tagValue = postTagFilter.trim();
        if (tagValue) {
          params.append('tag_id', tagValue);
        }
        if (sortPostsByRating) {
          params.append('sort_by_rating', 'true');
          params.append('sort_order', sortPostsOrder);
        }
        const url = `${config.GATEWAY_URL}/posts/by-problem/enriched/${problem.id}?${params.toString()}`;
        const resp = await axios.get(url, {
          headers: { Authorization: `Bearer ${auth.access_token}` },
        });
        setPosts(resp.data);
        setPostsError('');
      } catch (err) {
        setPostsError('Ошибка загрузки постов.');
      } finally {
        setPostsLoading(false);
      }
    };
    fetchPosts();
  }, [problem?.id, postOffset, postTagFilter, sortPostsByRating, sortPostsOrder, auth.access_token]);


  const handlePostPrev = () => {
    if (postOffset >= postLimit) {
      setPostOffset(postOffset - postLimit);
    }
  };

  const handlePostNext = () => {
    if (posts.length === postLimit) {
      setPostOffset(postOffset + postLimit);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Вы уверены, что хотите удалить эту задачу?')) {
      try {
        await axios.delete(`${config.GATEWAY_URL}/problems/${problem.id}`, {
          headers: { Authorization: `Bearer ${auth.access_token}` },
        });
        navigateToProblems();
      } catch (err) {
        setError('Ошибка при удалении задачи.');
      }
    }
  };

  const handleEditChange = (e) => {
    setEditData({ ...editData, [e.target.name]: e.target.value });
  };

  const handleTestCaseChange = (index, field, value) => {
    const newCases = [...editData.test_cases];
    newCases[index][field] = value;
    setEditData({ ...editData, test_cases: newCases });
  };

  const addTestCase = () => {
    setEditData({
      ...editData,
      test_cases: [...editData.test_cases, { input_data: '', output_data: '' }],
    });
  };

  const handleDeleteTestCase = (index) => {
    const newCases = editData.test_cases.filter((_, i) => i !== index);
    setEditData({ ...editData, test_cases: newCases });
  };

  const handleReaction = async (reactionType) => {
    try {
      await axios.post(
        `${config.GATEWAY_URL}/reactions/`,
        {
          target_id: problem.id,
          target_type: "problem",
          reaction_type: reactionType,
        },
        { headers: { Authorization: `Bearer ${auth.access_token}` } }
      );
      const url = auth.currentUser
        ? `${config.GATEWAY_URL}/problems/${problem.id}?user_id=${auth.currentUser.keycloak_id}`
        : `${config.GATEWAY_URL}/problems/${problem.id}`;
      const resp = await axios.get(url, { headers: { Authorization: `Bearer ${auth.access_token}` } });
      setProblem(resp.data);
    } catch (err) {
    }
  };

  const handleSaveEdit = async () => {
    try {
      const url = `${config.GATEWAY_URL}/problems/${problem.id}`;
      const resp = await axios.put(url, editData, {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      setProblem(resp.data);
      setIsEditing(false);
    } catch (err) {
      if (err.response) {
      }
      setError('Ошибка обновления задачи.');
    }
  };

  const handleCancelEdit = () => {
    setEditData({
      title: problem.title,
      description: problem.description,
      difficulty: problem.difficulty,
      time_limit: problem.time_limit,
      memory_limit: problem.memory_limit,
      test_cases: problem.test_cases,
      tags: problem.tags || [],
    });
    setIsEditing(false);
  };

  const handleLanguageChange = (e) => {
    setLanguage(e.target.value);
  };

  const handleAttachTag = async () => {
    if (!selectedTagToAttach) return;
    try {
      await axios.post(
        `${config.GATEWAY_URL}/problems/${problem.id}/tags/${selectedTagToAttach}`,
        {},
        { headers: { Authorization: `Bearer ${auth.access_token}` } }
      );
      const tagToAdd = availableTags.find(
        (tag) => tag.id === selectedTagToAttach
      );
      if (tagToAdd && !editData.tags.some((t) => t.id === tagToAdd.id)) {
        setEditData({ ...editData, tags: [...editData.tags, tagToAdd] });
      }
      setSelectedTagToAttach('');
    } catch (err) {
      setError('Ошибка при прикреплении тега.');
    }
  };

  const handleDetachTag = async (tagId) => {
    try {
      await axios.delete(
        `${config.GATEWAY_URL}/problems/${problem.id}/tags/${tagId}`,
        { headers: { Authorization: `Bearer ${auth.access_token}` } }
      );
      const newTags = editData.tags.filter((tag) => tag.id !== tagId);
      setEditData({ ...editData, tags: newTags });
    } catch (err) {
      setError('Ошибка при откреплении тега.');
    }
  };

  const handleCreatePost = () => {
    navigate(`/posts/create?problem_id=${problem.id}`);
  };

  if (loading) {
    return (
      <Container component="main" sx={{ py: 8 }}>
        <CssBaseline />
        <Typography variant="h6" align="center">
          Загрузка...
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

  if (!problem) {
    return (
      <Container component="main" sx={{ py: 8 }}>
        <CssBaseline />
        <Typography variant="h6" align="center">
          Задача не найдена.
        </Typography>
      </Container>
    );
  }

  return (
    <Container component="main" sx={{ py: 4 }}>
      <CssBaseline />
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          gap: 4,
          alignItems: 'stretch',
        }}
      >
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <Paper
            elevation={3}
            sx={{
              p: 3,
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {isEditing ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, height: '100%' }}>
                <TextField
                  label="Название"
                  name="title"
                  value={editData.title}
                  onChange={handleEditChange}
                  required
                />
                <TextField
                  label="Описание"
                  name="description"
                  value={editData.description}
                  onChange={handleEditChange}
                  multiline
                  rows={4}
                  required
                />
                <FormControl fullWidth>
                  <InputLabel id="difficulty-select-label">Сложность</InputLabel>
                  <Select
                    labelId="difficulty-select-label"
                    name="difficulty"
                    value={editData.difficulty}
                    label="Сложность"
                    onChange={handleEditChange}
                  >
                    <MenuItem value="EASY">EASY</MenuItem>
                    <MenuItem value="MEDIUM">MEDIUM</MenuItem>
                    <MenuItem value="HARD">HARD</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  label="Лимит времени (секунд)"
                  name="time_limit"
                  type="number"
                  value={editData.time_limit}
                  onChange={handleEditChange}
                  required
                />
                <TextField
                  label="Лимит памяти (МБ)"
                  name="memory_limit"
                  type="number"
                  value={editData.memory_limit}
                  onChange={handleEditChange}
                  required
                />

                <Typography variant="h6">Тест-кейсы</Typography>
                {editData.test_cases.map((tc, index) => (
                  <Box key={index} sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                    <TextField
                      label="Входные данные"
                      value={tc.input_data}
                      onChange={(e) => handleTestCaseChange(index, 'input_data', e.target.value)}
                      required
                      fullWidth
                    />
                    <TextField
                      label="Выходные данные"
                      value={tc.output_data}
                      onChange={(e) => handleTestCaseChange(index, 'output_data', e.target.value)}
                      required
                      fullWidth
                    />
                    <IconButton onClick={() => handleDeleteTestCase(index)}>
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                ))}
                <Button variant="outlined" onClick={addTestCase}>
                  Добавить тест-кейс
                </Button>

                <Typography variant="h6">Теги</Typography>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                  <FormControl fullWidth>
                    <InputLabel id="attach-tag-label">Прикрепить тег</InputLabel>
                    <Select
                      labelId="attach-tag-label"
                      value={selectedTagToAttach}
                      label="Прикрепить тег"
                      onChange={(e) => setSelectedTagToAttach(e.target.value)}
                    >
                      <MenuItem value="">
                        <em>Выберите тег</em>
                      </MenuItem>
                      {availableTags
                        .filter((tag) => !editData.tags.some((t) => t.id === tag.id))
                        .map((tag) => (
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
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {editData.tags.map((tag) => (
                    <Chip
                      key={tag.id}
                      label={tag.name}
                      onDelete={() => handleDetachTag(tag.id)}
                      variant="outlined"
                      size="small"
                    />
                  ))}
                </Box>

                <Box sx={{ display: 'flex', gap: 2, mt: 'auto' }}>
                  <Button variant="contained" onClick={handleSaveEdit}>
                    Сохранить
                  </Button>
                  <Button variant="outlined" onClick={handleCancelEdit}>
                    Отмена
                  </Button>
                </Box>
              </Box>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <Typography variant="h4" gutterBottom>
                  {problem.title}
                </Typography>
                <Typography variant="subtitle1" gutterBottom>
                  Автор:{" "}
                  <Link to={`/profile/${problem.created_by}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                    {author && author.display_name}
                  </Link>
                </Typography>
                <ReactMarkdown>
                  {problem.description}
                </ReactMarkdown>
                <Box sx={{ mt: 'auto' }}>
                  <Box sx={{ mb: 2 }}>
                    <Chip
                      label={problem.difficulty}
                      color={difficultyColorMapping[problem.difficulty] || 'default'}
                      size="small"
                    />
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                    <Chip
                      label={`${problem.time_limit} с`}
                      size="small"
                      sx={{ backgroundColor: grey[200], color: 'black' }}
                    />
                    <Chip
                      label={`${problem.memory_limit} МБ`}
                      size="small"
                      sx={{ backgroundColor: grey[200], color: 'black' }}
                    />
                  </Box>
                  {problem.tags && problem.tags.length > 0 && (
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {problem.tags.map((tag) => (
                        <Chip key={tag.id} label={tag.name} size="small" variant="outlined" />
                      ))}
                    </Box>
                  )}
                  <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 2 }}>
                    <Chip
                      label={`Рейтинг: ${problem.reaction_balance > 0 ? `+${problem.reaction_balance}` : problem.reaction_balance}`}
                      size="small"
                      color={problem.reaction_balance > 0 ? 'success' : (problem.reaction_balance < 0 ? 'error' : 'warning')}
                    />
                    <Button
                      variant={problem.user_reaction === 'plus' ? 'contained' : 'outlined'}
                      color="success"
                      size="small"
                      onClick={() => handleReaction('plus')}
                    >
                      +
                    </Button>
                    <Button
                      variant={problem.user_reaction === 'minus' ? 'contained' : 'outlined'}
                      color="error"
                      size="small"
                      onClick={() => handleReaction('minus')}
                    >
                      –
                    </Button>
                  </Box>
                  <Box sx={{ textAlign: 'right', mt: 1, display: 'flex', flexDirection: 'column' }}>
                    <Typography variant="caption" color="text.secondary">
                      Создано: {new Date(problem.created_at).toLocaleString()}
                    </Typography>
                    {problem.updated_at && (
                      <Typography variant="caption" color="text.secondary">
                        Обновлено: {new Date(problem.updated_at).toLocaleString()}
                      </Typography>
                    )}
                  </Box>

                </Box>
              </Box>
            )}
          </Paper>
          {canEdit && !isEditing && (
            <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
              <Button variant="contained" onClick={() => setIsEditing(true)}>
                Редактировать
              </Button>
              <Button variant="outlined" color="error" onClick={handleDelete}>
                Удалить
              </Button>
            </Box>
          )}
        </Box>




        {/* Правая колонка: Редактор кода */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <Paper
            elevation={3}
            sx={{
              p: 3,
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
              <Button
                variant={!showMySolutions ? 'contained' : 'outlined'}
                onClick={() => setShowMySolutions(false)}
                sx={{ mr: 1 }}
              >
                Редактор кода
              </Button>
              <Button
                variant={showMySolutions ? 'contained' : 'outlined'}
                onClick={() => setShowMySolutions(true)}
              >
                Мои решения
              </Button>
            </Box>

            {showMySolutions ? (
              <Box sx={{ flexGrow: 1, minHeight: '300px', mb: 2, overflow: 'auto' }}>
                {solutionsLoading ? (
                  <Typography>Загрузка решений...</Typography>
                ) : solutionsError ? (
                  <Typography color="error">{solutionsError}</Typography>
                ) : mySolutions.length > 0 ? (
                  mySolutions.map((solution) => (
                    <Paper
                      key={solution.id}
                      elevation={1}
                      sx={{
                        p: 2,
                        mb: 1,
                        cursor: 'pointer',
                      }}
                      onClick={() => navigate(`/solutions/${solution.id}`)}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                          {solution.language.toUpperCase()}
                        </Typography>
                        <Chip
                          label={solution.status}
                          size="small"
                          color={
                            solution.status === 'AC'
                              ? 'success'
                              : solution.status === 'pending'
                                ? 'default'
                                : 'error'
                          }
                        />
                      </Box>
                      <Typography variant="body2">
                        {new Date(solution.created_at).toLocaleString()}
                      </Typography>
                    </Paper>
                  ))
                ) : (
                  <Typography>Нет решений.</Typography>
                )}
              </Box>
            ) : (
              <>
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

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel id="language-select-label">Язык программирования</InputLabel>
                  <Select
                    labelId="language-select-label"
                    value={language}
                    label="Язык программирования"
                    onChange={handleLanguageChange}
                  >
                    <MenuItem value="python">Python</MenuItem>
                    <MenuItem value="java">Java</MenuItem>
                    <MenuItem value="javascript">JavaScript</MenuItem>
                    <MenuItem value="c_cpp">C++</MenuItem>
                  </Select>
                </FormControl>

                <Box sx={{ flexGrow: 1, minHeight: '300px', mb: 2 }}>
                  <AceEditor
                    mode={language}
                    theme="github"
                    name="code_editor"
                    onChange={(newCode) => setCode(newCode)}
                    fontSize={14}
                    showPrintMargin
                    showGutter
                    highlightActiveLine
                    value={code}
                    width="100%"
                    height="100%"
                    setOptions={{
                      useWorker: language === 'javascript' ? false : true,
                      showLineNumbers: true,
                      tabSize: 2,
                    }}
                  />
                </Box>

                <Box sx={{ textAlign: 'center' }}>
                  <Button variant="contained" onClick={handleSubmitSolution}>
                    Отправить решение
                  </Button>
                </Box>
              </>
            )}
          </Paper>

        </Box>
      </Box>

      <Box sx={{ mt: 4 }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
          }}
        >
          <Typography variant="h5" gutterBottom>
            Посты к задаче
          </Typography>
          <Button variant="contained" onClick={handleCreatePost}>
            Создать пост
          </Button>
        </Box>

        <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
          <Typography variant="body1">Сортировать посты по рейтингу:</Typography>
          <Switch
            checked={sortPostsByRating}
            onChange={(e) => {
              setSortPostsByRating(e.target.checked);
              setPostOffset(0);
            }}
            color="primary"
          />
          {sortPostsByRating && (
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel id="sort-posts-order-label">Порядок</InputLabel>
              <Select
                labelId="sort-posts-order-label"
                value={sortPostsOrder}
                label="Порядок"
                onChange={(e) => {
                  setSortPostsOrder(e.target.value);
                  setPostOffset(0);
                }}
              >
                <MenuItem value="asc">Возрастание</MenuItem>
                <MenuItem value="desc">Убывание</MenuItem>
              </Select>
            </FormControl>
          )}
        </Box>


        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel id="post-tag-filter-label">Фильтр по тегу</InputLabel>
            <Select
              labelId="post-tag-filter-label"
              value={postTagFilter}
              label="Фильтр по тегу"
              onChange={(e) => {
                setPostTagFilter(e.target.value);
                setPostOffset(0);
              }}
            >
              <MenuItem value="">
                <em>Все</em>
              </MenuItem>
              {availableTags.map((tag) => (
                <MenuItem key={tag.id} value={tag.id}>
                  {tag.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {postsLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
            <Typography>Загрузка постов...</Typography>
          </Box>
        ) : postsError ? (
          <Typography color="error">{postsError}</Typography>
        ) : (
          <Box>
            {posts.map((post) => (
              <Box
                key={post.id}
                sx={{
                  border: "1px solid",
                  borderColor: "divider",
                  borderRadius: 1,
                  p: 2,
                  mb: 1,
                  cursor: "pointer",
                  "&:hover": { backgroundColor: "action.hover" },
                }}
                onClick={() => navigate(`/posts/${post.id}`)}
              >
                <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {post.title}
                    {auth.currentUser && post.created_by === auth.currentUser.keycloak_id && (
                      <Tooltip title="Мой пост">
                        <AccountCircleIcon color="primary" fontSize="small" sx={{ ml: 1 }} />
                      </Tooltip>
                    )}
                  </Typography>
                  <Chip
                    label={formatReactionBalance(post.reaction_balance)}
                    size="small"
                    color={getReactionColor(post.reaction_balance)}
                  />
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Автор: {post.author_display_name} | {new Date(post.created_at).toLocaleString()}
                </Typography>
                {post.tags && post.tags.length > 0 && (
                  <Box sx={{ mt: 1, display: "flex", gap: 1, flexWrap: "wrap" }}>
                    {post.tags.map((tag) => (
                      <Chip key={tag.id} label={tag.name} size="small" variant="outlined" />
                    ))}
                  </Box>
                )}
              </Box>
            ))}
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mt: 2,
              }}
            >
              <Button variant="outlined" onClick={handlePostPrev} disabled={postOffset === 0}>
                Предыдущая
              </Button>
              <Typography variant="body2">
                Страница {(postOffset / postLimit) + 1}
              </Typography>
              <Button variant="outlined" onClick={handlePostNext} disabled={posts.length < postLimit}>
                Следующая
              </Button>
            </Box>
          </Box>
        )}
      </Box>
    </Container>
  );
}
