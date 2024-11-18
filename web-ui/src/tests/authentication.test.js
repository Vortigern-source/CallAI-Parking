import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthContextProvider } from '../context/AuthContext';
import Login from '../pages/Login';
import { api } from '../utils/api';

// Mock the API client
jest.mock('../utils/api', () => ({
  api: {
    login: jest.fn(),
    me: jest.fn(),
  },
}));

// Mock navigation
const mockedUsedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
   ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockedUsedNavigate,
}));

describe('Authentication Flow', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('renders login page', () => {
    render(
      <BrowserRouter>
        <AuthContextProvider>
          <Login />
        </AuthContextProvider>
      </BrowserRouter>
    );

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  test('handles successful admin login', async () => {
    // Mock successful login response
    api.login.mockResolvedValue({
      access_token: 'test-token',
      role: 'admin'
    });
    api.me.mockResolvedValue({
      username: 'testadmin',
      role: 'admin'
    });

    render(
      <BrowserRouter>
        <AuthContextProvider>
          <Login />
        </AuthContextProvider>
      </BrowserRouter>
    );

    // Fill out login form
    fireEvent.change(screen.getByLabelText(/username/i), { 
      target: { value: 'testadmin' } 
    });
    fireEvent.change(screen.getByLabelText(/password/i), { 
      target: { value: 'testpassword' } 
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    // Wait for navigation
    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith('testadmin', 'testpassword');
      expect(mockedUsedNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  test('handles login error', async () => {
    // Mock login failure
    api.login.mockRejectedValue(new Error('Login failed. Invalid credentials.'));

    render(
      <BrowserRouter>
        <AuthContextProvider>
          <Login />
        </AuthContextProvider>
      </BrowserRouter>
    );

    // Fill out login form
    fireEvent.change(screen.getByLabelText(/username/i), { 
      target: { value: 'wronguser' } 
    });
    fireEvent.change(screen.getByLabelText(/password/i), { 
      target: { value: 'wrongpassword' } 
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/login failed/i);
    });
  });

  test('prevents login with empty credentials', async () => {
    render(
      <BrowserRouter>
        <AuthContextProvider>
          <Login />
        </AuthContextProvider>
      </BrowserRouter>
    );

    // Submit form without filling credentials
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    // Check for error message
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/please enter both username and password/i);
    });
  });
});
