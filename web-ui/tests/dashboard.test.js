import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../src/context/AuthContext';
import Dashboard from '../src/pages/Dashboard';

// Mock useAuth hook
const mockLogout = jest.fn();
jest.mock('../src/context/AuthContext', () => ({
  ...jest.requireActual('../src/context/AuthContext'),
  useAuth: () => ({
    user: {
      username: 'testuser',
      role: 'admin'
    },
    logout: mockLogout
  })
}));

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));

describe('Dashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders dashboard with user information', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </BrowserRouter>
    );

    // Check user welcome message
    expect(screen.getByText(/Welcome, testuser/i)).toBeInTheDocument();
    
    // Check role display
    expect(screen.getByText(/Role: admin/i)).toBeInTheDocument();
  });

  test('admin panel button is enabled for admin users', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </BrowserRouter>
    );

    const adminPanelButton = screen.getByText(/Admin Panel/i);
    expect(adminPanelButton).toBeEnabled();
  });

  test('logout button functionality', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </BrowserRouter>
    );

    const logoutButton = screen.getByText(/Logout/i);
    fireEvent.click(logoutButton);

    // Verify logout function was called
    expect(mockLogout).toHaveBeenCalled();
    
    // Verify navigation to login page
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  test('admin panel button navigation', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </BrowserRouter>
    );

    const adminPanelButton = screen.getByText(/Admin Panel/i);
    fireEvent.click(adminPanelButton);

    // Verify navigation to admin dashboard
    expect(mockNavigate).toHaveBeenCalledWith('/admin/dashboard');
  });
});
