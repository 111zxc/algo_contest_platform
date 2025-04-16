import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { Box, Chip, Tooltip, Typography } from '@mui/material';
import React from 'react';
import { Link } from 'react-router-dom';


const difficultyColorMapping = {
  EASY: 'success',
  MEDIUM: 'warning',
  HARD: 'error',
};

const getReactionColor = (balance) => {
  if (balance > 0) return 'success';
  if (balance < 0) return 'error';
  return 'warning';
};

const formatReactionBalance = (balance) =>
  balance > 0 ? `+${balance}` : `${balance}`;

export default function ProblemRow({ problem, currentUserId, solved }) {
  return (
    <Box
      component={Link}
      to={`/problems/${problem.id}`}
      sx={{
        textDecoration: 'none',
        color: 'inherit',
        display: 'grid',
        gridTemplateColumns: '1fr auto auto auto',
        alignItems: 'center',
        gap: 2,
        py: 1,
        px: 2,
        borderBottom: '1px solid',
        borderColor: 'divider',
        '&:hover': { backgroundColor: 'action.hover' },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="subtitle1" fontWeight="bold">
          {problem.title}
        </Typography>
        {currentUserId && problem.created_by === currentUserId && (
          <Tooltip title="Моя задача">
            <AccountCircleIcon color="primary" fontSize="small" sx={{ ml: 1 }} />
          </Tooltip>
        )}
        {solved && (
          <Tooltip title="Задача выполнена">
            <CheckCircleIcon color="success" fontSize="small" sx={{ ml: 1 }} />
          </Tooltip>
        )}
      </Box>

      <Box>
        <Chip
          label={problem.difficulty}
          color={difficultyColorMapping[problem.difficulty] || 'default'}
          size="small"
        />
      </Box>

      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
        {problem.tags?.map((tag) => (
          <Chip key={tag.id} label={tag.name} size="small" variant="outlined" />
        ))}
      </Box>

      <Box sx={{ textAlign: 'right' }}>
        <Chip
          label={formatReactionBalance(problem.reaction_balance)}
          size="small"
          color={getReactionColor(problem.reaction_balance)}
        />
      </Box>
    </Box>
  );
}
