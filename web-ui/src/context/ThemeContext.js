import React, { createContext, useContext, useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { api } from '../utils/api';
import { useAuth } from './AuthContext';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const CustomThemeProvider = ({ children }) => {
  const [mode, setMode] = useState('light');
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    // Only load user settings when authenticated and not loading
    if (isAuthenticated && !isLoading) {
      const loadUserSettings = async () => {
        try {
          const settings = await api.getUserSettings();
          if (settings && settings.theme) {
            setMode(settings.theme);
          }
        } catch (error) {
          console.error('Failed to load theme settings:', error);
          // Fallback to light theme on error
          setMode('light');
        }
      };

      loadUserSettings();
    }
  }, [isAuthenticated, isLoading]); // Run when authentication status or loading state changes

  const theme = createTheme({
    palette: {
      mode,
    },
  });

  const toggleTheme = async () => {
    if (!isAuthenticated || isLoading) return; // Don't attempt to save if not authenticated or still loading

    const newMode = mode === 'light' ? 'dark' : 'light';
    try {
      await api.updateUserSettings({
        theme: newMode,
        language: 'en',
        notifications: true,
        dashboard_layout: {}
      });
      setMode(newMode);
    } catch (error) {
      console.error('Failed to update theme:', error);
    }
  };

  return (
    <ThemeContext.Provider value={{ mode, toggleTheme }}>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </ThemeContext.Provider>
  );
};