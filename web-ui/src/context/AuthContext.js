import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';
import { api } from '../utils/api';

export const AuthContext = createContext(null);

export const AuthContextProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [role, setRole] = useState(localStorage.getItem('role'));
  const [username, setUsername] = useState(localStorage.getItem('username'));
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const verifyToken = useCallback(async () => {
    if (token) {
      try {
        setIsLoading(true);
        const userData = await api.me();
        setIsAuthenticated(true);
        setRole(userData.role);
        setUsername(userData.username);
      } catch (error) {
        console.error('Token verification failed:', error);
        // Clear invalid token
        setToken(null);
        setRole(null);
        setUsername(null);
        setIsAuthenticated(false);
        localStorage.removeItem('token');
        localStorage.removeItem('role');
        localStorage.removeItem('username');
      } finally {
        setIsLoading(false);
      }
    } else {
      setIsAuthenticated(false);
      setIsLoading(false);
    }
  }, [token]);

  // Verify token on mount and token change
  useEffect(() => {
    verifyToken();
  }, [verifyToken]);

  const login = useCallback(({ token: newToken, role: newRole, username: newUsername }) => {
    console.log('Login data:', { newToken, newRole, newUsername });
    setToken(newToken);
    setRole(newRole);
    setUsername(newUsername);
    setIsAuthenticated(true);
    localStorage.setItem('token', newToken);
    localStorage.setItem('role', newRole);
    localStorage.setItem('username', newUsername);
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setRole(null);
    setUsername(null);
    setIsAuthenticated(false);
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('username');
  }, []);

  const isAdmin = useCallback(() => role === 'admin', [role]);

  const value = {
    token,
    role,
    username,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    isLoading,
    user: { token, role, username }
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the AuthContext
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
