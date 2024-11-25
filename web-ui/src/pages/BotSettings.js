import React, { useState, useEffect } from 'react';
import { 
    Box, 
    Typography, 
    Container, 
    Paper, 
    TextField, 
    Button, 
    Grid, 
    Divider,
    Alert,
    CircularProgress
} from '@mui/material';
import { api } from '../utils/api';

function BotSettings() {
    const [config, setConfig] = useState({
        prompts: {
            assistant_prompt: ''
        },
        discussion: {
            welcome_message: ''
        },
        environment_variables: {}
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        fetchBotConfig();
    }, []);

    const fetchBotConfig = async () => {
        try {
            setLoading(true);
            const response = await api.getBotConfig();
            
            // Ensure all sections are initialized
            const safeConfig = {
                prompts: response.prompts || { assistant_prompt: '' },
                discussion: response.discussion || { welcome_message: '' },
                environment_variables: response.environment_variables || {}
            };

            console.log('Fetched bot config:', safeConfig);
            setConfig(safeConfig);
            setLoading(false);
        } catch (err) {
            console.error('Error fetching bot config:', err);
            setError('Failed to load bot configuration');
            setLoading(false);
        }
    };

    const handleInputChange = (section, key, value) => {
        setConfig(prevConfig => ({
            ...prevConfig,
            [section]: {
                ...prevConfig[section],
                [key]: value
            }
        }));
    };

    const handleEnvironmentVariableChange = (key, value) => {
        setConfig(prevConfig => ({
            ...prevConfig,
            environment_variables: {
                ...prevConfig.environment_variables,
                [key]: value
            }
        }));
    };

    const handleSave = async () => {
        try {
            setLoading(true);
            await api.updateBotConfig(config);
            setSuccess('Bot configuration updated successfully');
            setError('');
        } catch (err) {
            console.error('Error updating bot config:', err);
            setError('Failed to update bot configuration');
            setSuccess('');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Container maxWidth="lg">
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                    <CircularProgress />
                </Box>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg">
            <Box sx={{ my: 4 }}>
                <Typography variant="h4" gutterBottom>
                    Bot Configuration
                </Typography>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                {success && (
                    <Alert severity="success" sx={{ mb: 2 }}>
                        {success}
                    </Alert>
                )}

                <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        Prompts
                    </Typography>
                    <TextField
                        fullWidth
                        multiline
                        rows={10}
                        label="Assistant Prompt"
                        variant="outlined"
                        value={config.prompts.assistant_prompt}
                        onChange={(e) => handleInputChange('prompts', 'assistant_prompt', e.target.value)}
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        fullWidth
                        label="Welcome Message"
                        variant="outlined"
                        value={config.discussion.welcome_message}
                        onChange={(e) => handleInputChange('discussion', 'welcome_message', e.target.value)}
                    />
                </Paper>

                <Paper elevation={3} sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        Environment Variables
                    </Typography>
                    <Grid container spacing={2}>
                        {config.environment_variables && Object.entries(config.environment_variables).map(([key, value]) => (
                            <Grid item xs={12} sm={6} key={key}>
                                <TextField
                                    fullWidth
                                    label={key}
                                    variant="outlined"
                                    value={value || ''}
                                    onChange={(e) => handleEnvironmentVariableChange(key, e.target.value)}
                                    type={key.includes('KEY') ? 'password' : 'text'}
                                />
                            </Grid>
                        ))}
                    </Grid>
                </Paper>

                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button 
                        variant="contained" 
                        color="primary" 
                        onClick={handleSave}
                        disabled={loading}
                    >
                        Save Configuration
                    </Button>
                </Box>
            </Box>
        </Container>
    );
}

export default BotSettings;
