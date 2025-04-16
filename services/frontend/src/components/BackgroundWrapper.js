import { Box } from '@mui/material';
import React from 'react';

export default function BackgroundWrapper({ children, sx }) {
  return (
    <Box
      component="div"
      sx={(theme) => ({
        position: 'relative',
        minHeight: '100vh',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          display: 'block',
          position: 'absolute',
          zIndex: -1,
          inset: 0,
          backgroundImage:
            'radial-gradient(ellipse at 50% 50%, hsl(210, 100%, 97%), hsl(0, 0%, 100%))',
          backgroundRepeat: 'no-repeat',
          ...theme.applyStyles('dark', {
            backgroundImage:
              'radial-gradient(at 50% 50%, hsla(210, 100%, 16%, 0.5), hsl(220, 30%, 5%))',
          }),
        },
        ...sx,
      })}
    >
      {children}
    </Box>
  );
}
