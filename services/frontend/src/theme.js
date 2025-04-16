import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#007BFF', // акцентный цвет для интерактивных элементов
    },
    secondary: {
      main: '#333333', // для второстепенных элементов
    },
    background: {
      default: '#F7F7F7', // светлый, почти белый фон
    },
    text: {
      primary: '#333333',
      secondary: '#666666',
    },
  },
  typography: {
    fontFamily: 'Roboto, Montserrat, sans-serif',
  },
});

export default theme;
