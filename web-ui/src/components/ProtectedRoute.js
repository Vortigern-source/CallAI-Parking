import React, { useContext } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { AuthContext } from '../context/AuthContext';

export default function ProtectedRoute({ children, requireAdmin }) {
  const { isAuthenticated, role, isLoading } = useContext(AuthContext);
  const location = useLocation();

  if (isLoading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
        bgcolor="#f5f5f5"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login page with return url
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && role !== 'admin') {
    // Redirect unauthorized users to home page
    return <Navigate to="/" replace />;
  }

  return children;
}