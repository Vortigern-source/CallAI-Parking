import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext(null);

export const AuthContextProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [token, setToken] = useState(null);
    const navigate = useNavigate();

    const logout = useCallback(() => {
        // Clear localStorage
        localStorage.removeItem('token');
        localStorage.removeItem('user');

        setUser(null);
        setToken(null);
        setIsAuthenticated(false);
        navigate('/login');
    }, [navigate]);

    const isAdmin = useCallback(() => {
        return user?.role === 'admin';
    }, [user]);

    useEffect(() => {
        // Check for existing token in localStorage on initial load
        const storedToken = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');

        if (storedToken && storedUser) {
            try {
                const parsedUser = JSON.parse(storedUser);
                setUser(parsedUser);
                setToken(storedToken);
                setIsAuthenticated(true);
            } catch (error) {
                console.error('Error parsing user data', error);
                logout();
            }
        }
        setIsLoading(false);
    }, [logout]);

    const login = (userData) => {
        // Store token and user info in localStorage
        localStorage.setItem('token', userData.token);
        localStorage.setItem('user', JSON.stringify({
            username: userData.username,
            role: userData.role
        }));

        setUser({
            username: userData.username,
            role: userData.role
        });
        setToken(userData.token);
        setIsAuthenticated(true);
    };

    return (
        <AuthContext.Provider value={{ 
            user, 
            isAuthenticated, 
            isLoading, 
            token,
            login, 
            logout,
            isAdmin
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthContextProvider');
    }
    return context;
};
