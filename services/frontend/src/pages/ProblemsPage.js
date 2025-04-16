import {
  Box,
  Button,
  CircularProgress,
  Container,
  CssBaseline,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Switch,
  Typography,
} from '@mui/material';
import axios from 'axios';
import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ProblemRow from '../components/ProblemRow';
import config from '../config';
import { AuthContext } from '../context/AuthContext';

export default function ProblemsPage() {
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [offset, setOffset] = useState(0);
  const limit = 10;

  const [difficultyFilter, setDifficultyFilter] = useState('');
  const [tagFilter, setTagFilter] = useState('');

  const [availableTags, setAvailableTags] = useState([]);

  const [sortByRating, setSortByRating] = useState(false);
  const [sortOrder, setSortOrder] = useState('desc');

  const [solvedTasks, setSolvedTasks] = useState([]);



  const navigate = useNavigate();
  const { auth } = useContext(AuthContext);

  const fetchAvailableTags = async () => {
    try {
      const resp = await axios.get(`${config.GATEWAY_URL}/tags/`, {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      setAvailableTags(resp.data);
    } catch (err) {
    }
  };

  useEffect(() => {
    if (auth.currentUser?.keycloak_id) {
      axios.get(`${config.GATEWAY_URL}/users/solved/${auth.currentUser.keycloak_id}`)
        .then((response) => {
          setSolvedTasks(response.data);
        })
        .catch((err) => {
        });
    }
  }, [auth.currentUser]);


  useEffect(() => {
    const fetchProblems = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        params.append('offset', offset);
        params.append('limit', limit);
        if (difficultyFilter) {
          params.append('difficulty', difficultyFilter);
        }
        if (tagFilter) {
          params.append('tag_id', tagFilter);
        }
        if (sortByRating) {
          params.append('sort_by_rating', 'true');
          params.append('sort_order', sortOrder);
        }

        const resp = await axios.get(`${config.GATEWAY_URL}/problems/enriched?${params.toString()}`, {
          headers: { Authorization: `Bearer ${auth.access_token}` },
        });
        setProblems(resp.data);
      } catch (err) {
        setError('Ошибка загрузки задач');
      } finally {
        setLoading(false);
      }
    };

    fetchProblems();
  }, [offset, difficultyFilter, tagFilter, sortByRating, sortOrder, auth.access_token]);


  useEffect(() => {
    fetchAvailableTags();
  }, [auth.access_token]);

  const handlePrev = () => {
    if (offset >= limit) {
      setOffset(offset - limit);
    }
  };

  const handleNext = () => {
    if (problems.length === limit) {
      setOffset(offset + limit);
    }
  };

  return (
    <Container component="main" sx={{ py: 8 }}>
      <CssBaseline />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 4
        }}
      >
        <Typography variant="h4" gutterBottom>
          Все задачи
        </Typography>
        <Button variant="contained" onClick={() => navigate('/problems/create')}>
          Создать задачу
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel id="difficulty-filter-label">Сложность</InputLabel>
          <Select
            labelId="difficulty-filter-label"
            value={difficultyFilter}
            label="Сложность"
            onChange={(e) => { setDifficultyFilter(e.target.value); setOffset(0); }}
          >
            <MenuItem value="">
              <em>Все</em>
            </MenuItem>
            <MenuItem value="EASY">EASY</MenuItem>
            <MenuItem value="MEDIUM">MEDIUM</MenuItem>
            <MenuItem value="HARD">HARD</MenuItem>
          </Select>
        </FormControl>
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel id="tag-filter-label">Тег</InputLabel>
          <Select
            labelId="tag-filter-label"
            value={tagFilter}
            label="Тег"
            onChange={(e) => { setTagFilter(e.target.value); setOffset(0); }}
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

      <Box sx={{ display: 'flex', gap: 2, mb: 4, alignItems: 'center' }}>
        <Typography variant="body1">Сортировать по рейтингу:</Typography>
        <Switch
          checked={sortByRating}
          onChange={(e) => { setSortByRating(e.target.checked); setOffset(0); }}
          color="primary"
        />
        {sortByRating && (
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel id="sort-order-label">Порядок</InputLabel>
            <Select
              labelId="sort-order-label"
              value={sortOrder}
              label="Порядок"
              onChange={(e) => { setSortOrder(e.target.value); setOffset(0); }}
            >
              <MenuItem value="asc">Возрастание</MenuItem>
              <MenuItem value="desc">Убывание</MenuItem>
            </Select>
          </FormControl>
        )}
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
          {problems.map((problem) => (
            <ProblemRow
              key={problem.id}
              problem={problem}
              currentUserId={auth.currentUser?.keycloak_id}
              solved={solvedTasks.includes(problem.id)}
            />
          ))}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mt: 4
            }}
          >
            <Button variant="outlined" onClick={handlePrev} disabled={offset === 0}>
              Предыдущая
            </Button>
            <Typography variant="body2">
              Страница {(offset / limit) + 1}
            </Typography>
            <Button variant="outlined" onClick={handleNext} disabled={problems.length < limit}>
              Следующая
            </Button>
          </Box>
        </Box>
      )}
    </Container>
  );
}
