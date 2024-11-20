import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { CustomThemeProvider } from './context/ThemeContext';
import CssBaseline from '@mui/material/CssBaseline';

// Context Providers
import { AuthContextProvider } from './context/AuthContext';

// Protected Route Component
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Bookings from './pages/Bookings';
import AdminUsers from './pages/AdminUsers';
import AdminManagement from './pages/AdminManagement';
import BotSettings from './pages/BotSettings';
import CallLogs from './pages/CallLogs';
import Settings from './pages/Settings';
import Functions from './pages/Functions';

function App() {
  return (
    <Router>
      <CustomThemeProvider>
        <AuthContextProvider>
          <CssBaseline />
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />

            {/* Protected Routes with Layout */}
            <Route element={<Layout />}>
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/bookings" 
                element={
                  <ProtectedRoute>
                    <Bookings />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/admin/users" 
                element={
                  <ProtectedRoute adminOnly>
                    <AdminUsers />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/admin/management" 
                element={
                  <ProtectedRoute adminOnly>
                    <AdminManagement />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/bot-settings" 
                element={
                  <ProtectedRoute>
                    <BotSettings />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/call-logs" 
                element={
                  <ProtectedRoute>
                    <CallLogs />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/settings" 
                element={
                  <ProtectedRoute>
                    <Settings />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/functions" 
                element={
                  <ProtectedRoute>
                    <Functions />
                  </ProtectedRoute>
                } 
              />
            </Route>

            {/* Redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AuthContextProvider>
      </CustomThemeProvider>
    </Router>
  );
}

export default App;
