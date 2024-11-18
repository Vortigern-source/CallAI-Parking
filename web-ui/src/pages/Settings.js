import React, { useState, useEffect } from 'react';
import { 
    Container, 
    Typography, 
    Grid, 
    Paper, 
    TextField, 
    Button, 
    Divider, 
    Switch, 
    FormControlLabel,
    Alert,
    Snackbar
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { api } from '../utils/api';

function Settings() {
    const { user } = useAuth();
    const { mode, toggleTheme } = useTheme();
    const [profile, setProfile] = useState({
        username: '',
        email: '',
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    });
    const [settings, setSettings] = useState({
        notifications: true,
        twoFactorAuth: false,
        language: 'en'
    });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchUserProfile = async () => {
            try {
                const userData = await api.me();
                setProfile(prev => ({
                    ...prev,
                    username: userData.username,
                    email: userData.email
                }));
            } catch (err) {
                setError('Failed to fetch user profile');
            }
        };

        const fetchUserSettings = async () => {
            try {
                const userSettings = await api.getUserSettings();
                setSettings({
                    notifications: userSettings.notifications,
                    twoFactorAuth: false,
                    language: userSettings.language
                });
            } catch (err) {
                setError('Failed to fetch user settings');
            }
        };

        fetchUserProfile();
        fetchUserSettings();
    }, []);

    const handleProfileUpdate = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        // Validate password change
        if (profile.newPassword !== profile.confirmPassword) {
            setError('New passwords do not match');
            setLoading(false);
            return;
        }

        try {
            await api.put('/profile', {
                email: profile.email,
                currentPassword: profile.currentPassword,
                newPassword: profile.newPassword
            });
            setSuccess('Profile updated successfully');
            // Clear password fields
            setProfile(prev => ({
                ...prev,
                currentPassword: '',
                newPassword: '',
                confirmPassword: ''
            }));
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to update profile');
        } finally {
            setLoading(false);
        }
    };

    const handleSettingsUpdate = async () => {
        try {
            await api.updateUserSettings({
                theme: mode,
                notifications: settings.notifications,
                language: settings.language,
                dashboard_layout: {}
            });
            setSuccess('Settings updated successfully');
        } catch (err) {
            setError('Failed to update settings');
        }
    };

    const handleSettingToggle = (setting) => {
        if (setting === 'theme') {
            toggleTheme();
        } else {
            setSettings(prev => ({
                ...prev,
                [setting]: !prev[setting]
            }));
        }
    };

    return (
        <Container maxWidth="md">
            <Snackbar 
                open={!!error} 
                autoHideDuration={6000} 
                onClose={() => setError('')}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert onClose={() => setError('')} severity="error">
                    {error}
                </Alert>
            </Snackbar>
            <Snackbar 
                open={!!success} 
                autoHideDuration={6000} 
                onClose={() => setSuccess('')}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert onClose={() => setSuccess('')} severity="success">
                    {success}
                </Alert>
            </Snackbar>

            <Typography variant="h4" gutterBottom>
                Account Settings
            </Typography>

            <Grid container spacing={3}>
                {/* Profile Settings */}
                <Grid item xs={12}>
                    <Paper elevation={3} sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Profile Information
                        </Typography>
                        <form onSubmit={handleProfileUpdate}>
                            <Grid container spacing={2}>
                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        label="Username"
                                        value={profile.username}
                                        disabled
                                    />
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        label="Email"
                                        type="email"
                                        value={profile.email}
                                        onChange={(e) => setProfile(prev => ({
                                            ...prev,
                                            email: e.target.value
                                        }))}
                                        required
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <TextField
                                        fullWidth
                                        label="Current Password"
                                        type="password"
                                        value={profile.currentPassword}
                                        onChange={(e) => setProfile(prev => ({
                                            ...prev,
                                            currentPassword: e.target.value
                                        }))}
                                        helperText="Required to make changes"
                                    />
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        label="New Password"
                                        type="password"
                                        value={profile.newPassword}
                                        onChange={(e) => setProfile(prev => ({
                                            ...prev,
                                            newPassword: e.target.value
                                        }))}
                                        helperText="Leave blank if no change"
                                    />
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        label="Confirm New Password"
                                        type="password"
                                        value={profile.confirmPassword}
                                        onChange={(e) => setProfile(prev => ({
                                            ...prev,
                                            confirmPassword: e.target.value
                                        }))}
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <Button 
                                        type="submit" 
                                        variant="contained" 
                                        color="primary"
                                        disabled={loading}
                                    >
                                        Update Profile
                                    </Button>
                                </Grid>
                            </Grid>
                        </form>
                    </Paper>
                </Grid>

                {/* Application Settings */}
                <Grid item xs={12}>
                    <Paper elevation={3} sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Application Preferences
                        </Typography>
                        <Grid container spacing={2}>
                            <Grid item xs={12}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={mode === 'dark'}
                                            onChange={() => handleSettingToggle('theme')}
                                        />
                                    }
                                    label="Dark Mode"
                                />
                            </Grid>
                            <Grid item xs={12}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={settings.notifications}
                                            onChange={() => handleSettingToggle('notifications')}
                                        />
                                    }
                                    label="Enable Notifications"
                                />
                            </Grid>
                            <Grid item xs={12}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={settings.twoFactorAuth}
                                            onChange={() => handleSettingToggle('twoFactorAuth')}
                                        />
                                    }
                                    label="Two-Factor Authentication"
                                />
                            </Grid>
                            <Grid item xs={12}>
                                <Button 
                                    variant="contained" 
                                    color="primary"
                                    onClick={handleSettingsUpdate}
                                >
                                    Save Preferences
                                </Button>
                            </Grid>
                        </Grid>
                    </Paper>
                </Grid>
            </Grid>
        </Container>
    );
}

export default Settings;
