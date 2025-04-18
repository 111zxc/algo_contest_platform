import { Box, Button, Container, FormControl, InputLabel, MenuItem, Paper, Select, TextField, Typography } from '@mui/material';
import axios from 'axios';
import React, { useContext, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import config from '../config';
import { AuthContext } from '../context/AuthContext';

export default function CreateProblemPage() {
  const { auth } = useContext(AuthContext);
  const navigate = useNavigate();

  const { contestId } = useParams();

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    difficulty: 'EASY',
    time_limit: 1000000,
    memory_limit: 128,
  });
  const [testCases, setTestCases] = useState([
    { input_data: '', output_data: '' },
  ]);

  const [error, setError] = useState('');

  const handleInputChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleTestCaseChange = (index, field, value) => {
    const newCases = [...testCases];
    newCases[index][field] = value;
    setTestCases(newCases);
  };

  const addTestCase = () => {
    setTestCases([...testCases, { input_data: '', output_data: '' }]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        test_cases: testCases,
        ...(contestId ? { contest_id: contestId } : {})
      };
      await axios.post(`${config.GATEWAY_URL}/problems/`, payload, {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      if (contestId) {
        navigate(`/contests/${contestId}`);
      } else {
        navigate('/problems');
      }
    } catch (err) {
      setError('Ошибка при создании задачи');
    }
  };

  return (
    <Container component="main" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Создать задачу
        </Typography>
        {error && <Typography color="error">{error}</Typography>}
        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="Название задачи"
            name="title"
            value={formData.title}
            onChange={handleInputChange}
            required
          />
          <TextField
            label="Описание"
            name="description"
            multiline
            rows={4}
            value={formData.description}
            onChange={handleInputChange}
            required
          />
          <FormControl fullWidth>
            <InputLabel id="difficulty-label">Сложность</InputLabel>
            <Select
              labelId="difficulty-label"
              label="Сложность"
              name="difficulty"
              value={formData.difficulty}
              onChange={handleInputChange}
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
            value={formData.time_limit}
            onChange={handleInputChange}
            required
          />
          <TextField
            label="Лимит памяти (МБ)"
            name="memory_limit"
            type="number"
            value={formData.memory_limit}
            onChange={handleInputChange}
            required
          />

          <Typography variant="h6">Тест-кейсы</Typography>
          {testCases.map((testCase, index) => (
            <Box key={index} sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="Входные данные"
                value={testCase.input_data}
                onChange={(e) => handleTestCaseChange(index, 'input_data', e.target.value)}
                required
              />
              <TextField
                label="Выходные данные"
                value={testCase.output_data}
                onChange={(e) => handleTestCaseChange(index, 'output_data', e.target.value)}
                required
              />
            </Box>
          ))}
          <Button variant="outlined" onClick={addTestCase}>
            Добавить тест-кейс
          </Button>

          <Button variant="contained" type="submit">
            Создать задачу
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}
