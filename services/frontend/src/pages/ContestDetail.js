import {
    Alert,
    Box,
    Button,
    Chip,
    CircularProgress,
    Container,
    CssBaseline,
    Divider,
    List,
    ListItem,
    ListItemText,
    Paper,
    Snackbar,
    Typography
} from '@mui/material';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import axios from 'axios';
import React, { useContext, useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Link, useNavigate, useParams } from 'react-router-dom';
import config from '../config';
import { AuthContext } from '../context/AuthContext';

export default function ContestDetail() {
    const { contestId } = useParams();
    const { auth } = useContext(AuthContext);
    const navigate = useNavigate();

    const [contest, setContest] = useState(null);
    const [participants, setParticipants] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [joinLoading, setJoinLoading] = useState(false);
    const [joined, setJoined] = useState(false);
    const [error, setError] = useState('');
    const [notify, setNotify] = useState({ open: false, severity: 'info', message: '' });

    const [solutions, setSolutions] = useState([]);
    const [solOffset, setSolOffset] = useState(0);
    const solLimit = 10;
    const [solLoading, setSolLoading] = useState(false);
    const [solError, setSolError] = useState('');

    const [isEditingContest, setIsEditingContest] = useState(false);
    const [editContestData, setEditContestData] = useState({
        name: '',
        description: '',
        is_public: false,
    });
    const [newParticipantId, setNewParticipantId] = useState('');


    useEffect(() => {
        const fetchAll = async () => {
            setLoading(true);
            try {
                const contestResp = await axios.get(
                    `${config.GATEWAY_URL}/contests/${contestId}`,
                    { headers: auth.access_token ? { Authorization: `Bearer ${auth.access_token}` } : {} }
                );
                setContest(contestResp.data);

                const partResp = await axios.get(
                    `${config.GATEWAY_URL}/contests/${contestId}/participants`,
                    { headers: { Authorization: `Bearer ${auth.access_token}` } }
                );
                setParticipants(partResp.data);

                const taskResp = await axios.get(
                    `${config.GATEWAY_URL}/contests/${contestId}/tasks`,
                    { headers: auth.access_token ? { Authorization: `Bearer ${auth.access_token}` } : {} }
                );
                setTasks(taskResp.data);

                const me = auth.currentUser?.keycloak_id;
                if (me && partResp.data.some((p) => p.keycloak_id === me)) {
                    setJoined(true);
                }
            } catch (err) {
                console.error(err);
                setError('Не удалось загрузить данные контеста.');
            } finally {
                setLoading(false);
            }
        };

        fetchAll();
    }, [contestId, auth.access_token, auth.currentUser]);

    useEffect(() => {
        if (contest) {
            setEditContestData({
                name: contest.name,
                description: contest.description,
                is_public: contest.is_public,
            });
        }
    }, [contest]);


    useEffect(() => {
        if (!(auth.isAdmin || auth.currentUser?.keycloak_id === contest.created_by)) return;
        setSolLoading(true);
        axios.get(
            `${config.GATEWAY_URL}/solutions/${contestId}/solutions?offset=${solOffset}&limit=${solLimit}`,
            { headers: { Authorization: `Bearer ${auth.access_token}` } }
        )
            .then(resp => {
                setSolutions(resp.data);
                setSolError('');
            })
            .catch(() => {
                setSolError('Ошибка загрузки решений.');
            })
            .finally(() => setSolLoading(false));
    }, [contestId, solOffset, auth.access_token, auth.isAdmin, auth.currentUser]);


    const handleJoin = async () => {
        setJoinLoading(true);
        try {
            await axios.post(
                `${config.GATEWAY_URL}/contests/${contestId}/join`,
                {},
                { headers: { Authorization: `Bearer ${auth.access_token}` } }
            );
            setNotify({ open: true, severity: 'success', message: 'Вы вступили в контест!' });
            const partResp = await axios.get(
                `${config.GATEWAY_URL}/contests/${contestId}/participants`,
                { headers: { Authorization: `Bearer ${auth.access_token}` } }
            );
            setParticipants(partResp.data);
            setJoined(true);
        } catch (err) {
            console.error(err);
            setNotify({ open: true, severity: 'error', message: 'Не удалось вступить в контест.' });
        } finally {
            setJoinLoading(false);
        }
    };

    if (loading) {
        return (
            <Container sx={{ py: 8, textAlign: 'center' }}>
                <CssBaseline />
                <CircularProgress />
            </Container>
        );
    }

    if (error || !contest) {
        return (
            <Container sx={{ py: 8, textAlign: 'center' }}>
                <CssBaseline />
                <Typography color="error">{error || 'Контест не найден.'}</Typography>
            </Container>
        );
    }

    return (
        <Container sx={{ py: 8 }}>
            <CssBaseline />

            <Paper sx={{ p: 3, mb: 4 }}>
                <Typography variant="h4" gutterBottom>
                    {contest.name}
                </Typography>
                <Box sx={{ mb: 2 }}>
                    <ReactMarkdown>{contest.description}</ReactMarkdown>
                </Box>
                <Typography variant="body2" color="text.secondary">
                    {contest.is_public ? 'Публичный' : 'Приватный'} &nbsp;|&nbsp;
                    Создан: {new Date(contest.created_at).toLocaleString()}
                    {contest.updated_at && (
                        <> &nbsp;|&nbsp; Обновлён: {new Date(contest.updated_at).toLocaleString()}</>
                    )}
                </Typography>

                {!joined && contest.is_public && auth.isAuthenticated && (
                    <Box sx={{ mt: 2 }}>
                        <Button
                            variant="contained"
                            onClick={handleJoin}
                            disabled={joinLoading}
                        >
                            {joinLoading ? 'Вступление...' : 'Вступить в контест'}
                        </Button>
                    </Box>
                )}
            </Paper>

            {(auth.isAdmin || auth.currentUser?.keycloak_id === contest.created_by) && (
                <Box sx={{ mb: 3 }}>
                    {isEditingContest ? (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <TextField
                                label="Название"
                                fullWidth
                                value={editContestData.name}
                                onChange={e =>
                                    setEditContestData(d => ({ ...d, name: e.target.value }))
                                }
                            />
                            <TextField
                                label="Описание"
                                fullWidth
                                multiline
                                minRows={4}
                                value={editContestData.description}
                                onChange={e =>
                                    setEditContestData(d => ({ ...d, description: e.target.value }))
                                }
                            />
                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={editContestData.is_public}
                                        onChange={e =>
                                            setEditContestData(d => ({
                                                ...d,
                                                is_public: e.target.checked
                                            }))
                                        }
                                    />
                                }
                                label={editContestData.is_public ? 'Публичный' : 'Приватный'}
                            />
                            <Box sx={{ display: 'flex', gap: 1 }}>
                                <Button
                                    variant="contained"
                                    size="small"
                                    onClick={async () => {
                                        try {
                                            await axios.put(
                                                `${config.GATEWAY_URL}/contests/${contestId}`,
                                                editContestData,
                                                { headers: { Authorization: `Bearer ${auth.access_token}` } }
                                            );
                                            setContest(d => ({ ...d, ...editContestData }));
                                            setIsEditingContest(false);
                                            setNotify({
                                                open: true,
                                                severity: 'success',
                                                message: 'Контест обновлён!'
                                            });
                                        } catch {
                                            setNotify({
                                                open: true,
                                                severity: 'error',
                                                message: 'Ошибка при обновлении.'
                                            });
                                        }
                                    }}
                                >
                                    Сохранить
                                </Button>
                                <Button
                                    variant="outlined"
                                    size="small"
                                    onClick={() => {
                                        setEditContestData({
                                            name: contest.name,
                                            description: contest.description,
                                            is_public: contest.is_public
                                        });
                                        setIsEditingContest(false);
                                    }}
                                >
                                    Отмена
                                </Button>
                            </Box>
                        </Box>
                    ) : (
                        <Button
                            variant="outlined"
                            size="small"
                            onClick={() => setIsEditingContest(true)}
                        >
                            Редактировать контест
                        </Button>
                    )}
                </Box>
            )}

            {(auth.isAdmin || auth.currentUser?.keycloak_id === contest.created_by) && (
                <Box sx={{ mb: 4, display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                        label="Keycloak ID"
                        size="small"
                        value={newParticipantId}
                        onChange={e => setNewParticipantId(e.target.value)}
                    />
                    <Button
                        variant="contained"
                        size="small"
                        onClick={async () => {
                            try {
                                await axios.post(
                                    `${config.GATEWAY_URL}/contests/${contestId}/participants`,
                                    { user_keycloak_id: newParticipantId },
                                    { headers: { Authorization: `Bearer ${auth.access_token}` } }
                                );
                                const resp = await axios.get(
                                    `${config.GATEWAY_URL}/contests/${contestId}/participants`,
                                    { headers: { Authorization: `Bearer ${auth.access_token}` } }
                                );
                                setParticipants(resp.data);
                                setNewParticipantId('');
                                setNotify({
                                    open: true,
                                    severity: 'success',
                                    message: 'Участник добавлен!'
                                });
                            } catch {
                                setNotify({
                                    open: true,
                                    severity: 'error',
                                    message: 'Не удалось добавить участника.'
                                });
                            }
                        }}
                    >
                        Добавить участника
                    </Button>
                </Box>
            )}



            <Divider sx={{ mb: 4 }} />

            <Box sx={{ mb: 4 }}>
                <Typography variant="h5" gutterBottom>Участники</Typography>
                {participants.length === 0 ? (
                    <Typography>Пока нет участников.</Typography>
                ) : (
                    <List dense>
                        {participants.map((p) => (
                            <ListItem key={p.keycloak_id}>
                                <ListItemText primary={p.display_name || p.username} />
                            </ListItem>
                        ))}
                    </List>
                )}
            </Box>

            <Divider sx={{ mb: 4 }} />

            <Box>
                <Typography variant="h5" gutterBottom>Задачи контеста</Typography>
                {(auth.isAdmin || auth.currentUser.keycloak_id === contest.created_by) && (
                    <Button
                        variant="contained"
                        onClick={() => navigate(`/contests/${contest.id}/create-task`)}
                    >
                        Создать задачу
                    </Button>
                )}
                {tasks.length === 0 ? (
                    <Typography>Нет задач.</Typography>
                ) : (
                    tasks.map((t) => (
                        <Paper key={t.id} sx={{ p: 2, mb: 2 }}>
                            <Typography variant="h6">
                                <Link
                                    to={`/problems/${t.id}`}
                                    style={{ textDecoration: 'none', color: 'inherit' }}
                                >
                                    {t.title}
                                </Link>
                            </Typography>
                            <Typography variant="body2" sx={{ mt: 1 }}>
                                {t.description.length > 200
                                    ? t.description.slice(0, 200) + '…'
                                    : t.description}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                Сложность: {t.difficulty} &nbsp;|&nbsp; Создано: {new Date(t.created_at).toLocaleString()}
                            </Typography>
                        </Paper>
                    ))
                )}
            </Box>

            {(auth.isAdmin || auth.currentUser?.keycloak_id === contest.created_by) && (
                <Box sx={{ mt: 6 }}>
                    <Typography variant="h5" gutterBottom>
                        Решения участников
                    </Typography>

                    {solLoading ? (
                        <CircularProgress size={24} />
                    ) : solError ? (
                        <Typography color="error">{solError}</Typography>
                    ) : solutions.length === 0 ? (
                        <Typography>Нет решений.</Typography>
                    ) : (
                        <Box>
                            {solutions.map(sol => {
                                // найдём название задачи
                                const task = tasks.find(t => t.id === sol.problem_id);
                                return (
                                    <Paper
                                        key={sol.id}
                                        component="div"
                                        onClick={() => navigate(`/solutions/${sol.id}`)}
                                        sx={{
                                            p: 2,
                                            mb: 1,
                                            cursor: 'pointer',
                                            '&:hover': { backgroundColor: 'action.hover' }
                                        }}
                                    >
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Typography>
                                                Автор: {sol.created_by /* или имя, если есть */}
                                                &nbsp;|&nbsp;
                                                Задача: {task?.title || sol.problem_id}
                                            </Typography>
                                            <Chip
                                                label={sol.status}
                                                size="small"
                                                color={
                                                    sol.status === 'AC'
                                                        ? 'success'
                                                        : sol.status === 'pending'
                                                            ? 'default'
                                                            : 'error'
                                                }
                                            />
                                        </Box>
                                    </Paper>
                                );
                            })}

                            {/* пагинация */}
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                                <Button
                                    variant="outlined"
                                    size="small"
                                    onClick={() => setSolOffset(o => Math.max(0, o - solLimit))}
                                    disabled={solOffset === 0}
                                >
                                    Предыдущие
                                </Button>
                                <Typography>Стр. {(solOffset / solLimit) + 1}</Typography>
                                <Button
                                    variant="outlined"
                                    size="small"
                                    onClick={() => setSolOffset(o => o + solLimit)}
                                    disabled={solutions.length < solLimit}
                                >
                                    Следующие
                                </Button>
                            </Box>
                        </Box>
                    )}
                </Box>
            )}



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
