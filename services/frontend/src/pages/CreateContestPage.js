import {
    Alert,
    Box,
    Button,
    Container,
    CssBaseline,
    FormControlLabel,
    Snackbar,
    Switch,
    TextField,
    Typography
} from '@mui/material';
import axios from 'axios';
import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import config from '../config';
import { AuthContext } from '../context/AuthContext';

export default function CreateContestPage() {
    const { auth } = useContext(AuthContext);
    const navigate = useNavigate();

    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [isPublic, setIsPublic] = useState(true);
    const [loading, setLoading] = useState(false);

    const [notify, setNotify] = useState({
        open: false,
        severity: 'success',
        message: '',
    });

    const handleSubmit = async () => {
        if (!name.trim() || !description.trim()) return;
        setLoading(true);
        try {
            await axios.post(
                `${config.GATEWAY_URL}/contests/`,
                {
                    name,
                    description,
                    is_public: isPublic,
                },
                {
                    headers: { Authorization: `Bearer ${auth.access_token}` },
                }
            );
            setNotify({ open: true, severity: 'success', message: 'Контест создан!' });
            setTimeout(() => navigate('/contests'), 500);
        } catch (err) {
            console.error(err);
            setNotify({ open: true, severity: 'error', message: 'Ошибка при создании контеста.' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container component="main" sx={{ py: 8 }}>
            <CssBaseline />
            <Box
                sx={{
                    maxWidth: 600,
                    mx: 'auto',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2,
                }}
            >
                <Typography variant="h4" align="center">
                    Создать контест
                </Typography>

                <TextField
                    label="Название"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    fullWidth
                />

                <TextField
                    label="Описание"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    fullWidth
                    multiline
                    minRows={4}
                />

                <FormControlLabel
                    control={
                        <Switch
                            checked={isPublic}
                            onChange={(e) => setIsPublic(e.target.checked)}
                        />
                    }
                    label={isPublic ? 'Публичный' : 'Приватный'}
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
