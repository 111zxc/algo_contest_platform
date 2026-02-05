import {
    Alert,
    Box,
    Button,
    Container,
    CssBaseline,
    Snackbar,
    TextField,
    Typography
} from '@mui/material';
import axios from 'axios';
import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import config from '../config';
import { AuthContext } from '../context/AuthContext';

export default function CreateBlogPostPage() {
    const { auth } = useContext(AuthContext);
    const navigate = useNavigate();

    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);

    const [notify, setNotify] = useState({
        open: false,
        severity: 'success',
        message: '',
    });

    const handleSubmit = async () => {
        if (!title.trim() || !description.trim()) return;
        setLoading(true);
        try {
            await axios.post(
                `${config.GATEWAY_URL}/blogposts/`,
                { title, description },
                { headers: { Authorization: `Bearer ${auth.access_token}` } }
            );
            setNotify({ open: true, severity: 'success', message: 'Пост создан!' });
            setTimeout(() => navigate('/'), 500);
        } catch (err) {
            console.error(err);
            setNotify({ open: true, severity: 'error', message: 'Ошибка при создании.' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container component="main" sx={{ py: 8 }}>
            <CssBaseline />
            <Box sx={{ maxWidth: 600, mx: 'auto', display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Typography variant="h4" align="center">Новый блог‑пост</Typography>

                <TextField
                    label="Заголовок"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    fullWidth
                />

                <TextField
                    label="Описание (Markdown)"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    fullWidth
                    multiline
                    minRows={6}
                />

                <Box sx={{ textAlign: 'center', mt: 2 }}>
                    <Button
                        variant="contained"
                        onClick={handleSubmit}
                        disabled={loading}
                    >
                        {loading ? 'Сохраняем...' : 'Создать'}
                    </Button>
                </Box>
            </Box>

            <Snackbar
                open={notify.open}
                autoHideDuration={4000}
                onClose={() => setNotify((n) => ({ ...n, open: false }))}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert
                    severity={notify.severity}
                    onClose={() => setNotify((n) => ({ ...n, open: false }))}
                    sx={{ width: '100%' }}
                >
                    {notify.message}
                </Alert>
            </Snackbar>
        </Container>
    );
}
