import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import HomeIcon from '@mui/icons-material/Home';
import MenuIcon from '@mui/icons-material/Menu';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import Divider from '@mui/material/Divider';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import MenuItem from '@mui/material/MenuItem';
import { alpha, styled } from '@mui/material/styles';
import Toolbar from '@mui/material/Toolbar';
import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const StyledToolbar = styled(Toolbar)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  flexShrink: 0,
  borderRadius: `calc(${theme.shape.borderRadius}px + 8px)`,
  backdropFilter: 'blur(24px)',
  border: '1px solid',
  borderColor: (theme.vars || theme).palette.divider,
  backgroundColor: theme.vars
    ? `rgba(${theme.vars.palette.background.defaultChannel} / 0.4)`
    : alpha(theme.palette.background.default, 0.4),
  boxShadow: (theme.vars || theme).shadows[1],
  padding: '8px 12px',
}));

const AppAppBar = () => {
  const navigate = useNavigate();
  const { auth, logout } = useContext(AuthContext);
  const [open, setOpen] = React.useState(false);

  const toggleDrawer = (newOpen) => () => {
    setOpen(newOpen);
  };

  const goTo = (path) => {
    navigate(path);
  };

  return (
    <AppBar
      position="fixed"
      enableColorOnDark
      sx={{
        boxShadow: 0,
        bgcolor: 'transparent',
        backgroundImage: 'none',
        mt: 'calc(var(--template-frame-height, 0px) + 28px)',
      }}
    >
      <Container maxWidth="lg">
        <StyledToolbar variant="dense" disableGutters>
          <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', px: 0 }}>
            <IconButton sx={{ color: 'black' }} onClick={() => goTo('/')}>
              <HomeIcon />
            </IconButton>
            <Box sx={{ display: { xs: 'none', md: 'flex' }, ml: 2 }}>
              <Button variant="text" size="small" sx={{ color: 'black' }} onClick={() => goTo('/problems')}>
                Задачи
              </Button>
              {auth.isAdmin && (
                <Button variant="text" size="small" sx={{ color: 'black' }} onClick={() => goTo('/tags')}>
                  Теги
                </Button>
              )}
            </Box>
          </Box>
          <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 2, alignItems: 'center' }}>
            {auth.isAuthenticated ? (
              <>
                <Button variant="text" size="small" sx={{ color: 'black' }} onClick={() => goTo('/profile')}>
                  Профиль
                </Button>
                <Button variant="outlined" size="small" sx={{ color: 'black', borderColor: 'black' }} onClick={logout}>
                  Выйти
                </Button>
              </>
            ) : (
              <>
                <Button variant="text" size="small" sx={{ color: 'black' }} onClick={() => goTo('/login')}>
                  Войти
                </Button>
                <Button variant="text" size="small" sx={{ color: 'black' }} onClick={() => goTo('/register')}>
                  Регистрация
                </Button>
              </>
            )}
          </Box>
          <Box sx={{ display: { xs: 'flex', md: 'none' }, gap: 1 }}>
            <IconButton aria-label="Menu button" onClick={toggleDrawer(true)} sx={{ color: 'black' }}>
              <MenuIcon />
            </IconButton>
            <Drawer
              anchor="top"
              open={open}
              onClose={toggleDrawer(false)}
              PaperProps={{
                sx: { top: 'var(--template-frame-height, 0px)' },
              }}
            >
              <Box sx={{ p: 2, backgroundColor: 'background.default' }}>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <IconButton onClick={toggleDrawer(false)}>
                    <CloseRoundedIcon />
                  </IconButton>
                </Box>
                <MenuItem onClick={() => goTo('/')}>Главная</MenuItem>
                <MenuItem onClick={() => goTo('/problems')}>Задачи</MenuItem>
                {auth.isAdmin && (
                  <MenuItem onClick={() => goTo('/tags')}>Теги</MenuItem>
                )}
                <Divider sx={{ my: 3 }} />
                {auth.isAuthenticated ? (
                  <>
                    <MenuItem onClick={() => goTo('/profile')}>
                      <Button variant="text" sx={{ color: 'black' }} fullWidth>
                        Профиль
                      </Button>
                    </MenuItem>
                    <MenuItem onClick={logout}>
                      <Button variant="text" sx={{ color: 'black' }} fullWidth>
                        Выйти
                      </Button>
                    </MenuItem>
                  </>
                ) : (
                  <>
                    <MenuItem onClick={() => goTo('/login')}>
                      <Button variant="text" sx={{ color: 'black' }} fullWidth>
                        Войти
                      </Button>
                    </MenuItem>
                    <MenuItem onClick={() => goTo('/register')}>
                      <Button variant="text" sx={{ color: 'black' }} fullWidth>
                        Регистрация
                      </Button>
                    </MenuItem>
                  </>
                )}
              </Box>
            </Drawer>
          </Box>
        </StyledToolbar>
      </Container>
    </AppBar>
  );
};

export default AppAppBar;
