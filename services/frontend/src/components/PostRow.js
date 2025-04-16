import { Box, Typography } from '@mui/material';
import React from 'react';
import { Link } from 'react-router-dom';

export default function PostRow({ post, displayName }) {
  return (
    <Box
      component={Link}
      to={`/posts/${post.id}`}
      sx={{
        textDecoration: 'none',
        color: 'inherit',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 1,
        p: 2,
        mb: 1,
        display: 'flex',
        flexDirection: 'column',
        gap: 0.5,
        '&:hover': { bgcolor: 'action.hover' },
      }}
    >
      <Typography variant="subtitle2" fontWeight="bold">
        {post.content.length > 50
          ? post.content.slice(0, 50) + '...'
          : post.content}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        Автор: {displayName}
      </Typography>
    </Box>
  );
}
