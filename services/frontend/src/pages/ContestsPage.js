import {
    Box,
    Button,
    CircularProgress,
    Container,
    CssBaseline,
    Paper,
    Typography
} from '@mui/material';
import axios from 'axios';
import React, { useContext, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import config from '../config';
import { AuthContext } from '../context/AuthContext';

export default function ContestsPage() {
    const { auth } = useContext(AuthContext);
    const navigate = useNavigate();

    const [mode, setMode] = useState('public'); // 'public' | 'my' | 'participate'
    const [contests, setContests] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const [offset, setOffset] = useState(0);
    const limit = 10;

    const fetchContests = async () => {
        setLoading(true);
        setError('');
        try {
            let url = '';
            let opts = {};
            if (mode === 'public') {
                url = `${config.GATEWAY_URL}/contests`;
                const params = new URLSearchParams({ offset, limit });
                url += `?${params.toString()}`;
            } else if (mode === 'my') {
                url = `${config.GATEWAY_URL}/contests/my`;
                opts.headers = { Authorization: `Bearer ${auth.access_token}` };
            } else if (mode === 'participate') {
                url = `${config.GATEWAY_URL}/contests/my_participate`;
                opts.headers = { Authorization: `Bearer ${auth.access_token}` };
            }
            const resp = await axios.get(url, opts);
            setContests(resp.data);
        } catch (err) {
            console.error(err);
            setError('Не удалось загрузить контесты.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchContests();
    }, [mode, offset]);

    const handlePrev = () => {
        if (offset >= limit) setOffset(offset - limit);
    };
    const handleNext = () => {
        if (contests.length === limit) setOffset(offset + limit);
    };

    const switchMode = (newMode) => {
        if (newMode !== mode) {
            setMode(newMode);
            setOffset(0);
        }
    };

    return (
        <Container component="main" sx={{ py: 8 }}>
            <CssBaseline />

            <Box sx={{ textAlign: 'center', mb: 4 }}>
                <Typography variant="h4">Контесты</Typography>
                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 2 }}>
                    <Button
                        variant={mode === 'public' ? 'contained' : 'outlined'}
                        onClick={() => switchMode('public')}
                    >
                        Публичные
                    </Button>
                    {auth.isAuthenticated && (
                        <>
                            <Button
                                variant={mode === 'my' ? 'contained' : 'outlined'}
                                onClick={() => switchMode('my')}
                            >
                                Мои
                            </Button>
                            <Button
                                variant={mode === 'participate' ? 'contained' : 'outlined'}
                                onClick={() => switchMode('participate')}
                            >
                                Участвую
                            </Button>
                        </>
                    )}
                </Box>
                {auth.isAuthenticated && (
                    <Box sx={{ mt: 3 }}>
                        <Button
                            variant="contained"
                            onClick={() => navigate('/contests/create')}
                        >
                            Создать контест
                        </Button>
                    </Box>
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

                    {contests.map((c) => (
                        <Paper key={c.id} sx={{ p: 2, mb: 2 }}>
                            <Typography variant="h6"><Link
                                to={`/contests/${c.id}`}
                                style={{ textDecoration: 'none', color: 'inherit' }}
                            >
                                {c.name}
                            </Link></Typography>
                            <Typography variant="body2" sx={{ mt: 1 }}>
                                {c.description}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                Создано: {new Date(c.created_at).toLocaleString()}
                            </Typography>
                        </Paper>
                    ))}

                    <Box
                        sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            mt: 4,
                        }}
                    >
                        <Button
                            variant="outlined"
                            onClick={handlePrev}
                            disabled={offset === 0}
                        >
                            Предыдущая
                        </Button>
                        <Typography>Страница {(offset / limit) + 1}</Typography>
                        <Button
                            variant="outlined"
                            onClick={handleNext}
                            disabled={contests.length < limit}
                        >
                            Следующая
                        </Button>
                    </Box>
                </Box>
            )}
        </Container>
    );
}
