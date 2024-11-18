import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import { AuthProvider } from '../src/context/AuthContext';
import Login from '../src/pages/Login';

// Mock axios
jest.mock('axios');

describe('Authentication Tests', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  test('Login form renders correctly', () => {
    render(
      <AuthProvider>
        <Login />
      </AuthProvider>
    );

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  test('Successful login redirects to dashboard', async () => {
    // Mock successful login response
    const mockLoginResponse = {
      data: {
        access_token: 'fake_token',
        token_type: 'bearer',
        role: 'admin'
      }
    };
    axios.post.mockResolvedValue(mockLoginResponse);

    const mockNavigate = jest.fn();
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate
    }));

    render(
      <AuthProvider>
        <Login />
      </AuthProvider>
    );

    // Fill out login form
    fireEvent.change(screen.getByLabelText(/username/i), { 
      target: { value: 'admin' } 
    });
    fireEvent.change(screen.getByLabelText(/password/i), { 
      target: { value: 'AdminInitialPassword123!' } 
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    // Wait for login process
    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        '/api/token', 
        expect.any(FormData), 
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      );
    });
  });

  test('Failed login shows error message', async () => {
    // Mock failed login response
    const mockErrorResponse = {
      response: {
        status: 401,
        data: { detail: 'Incorrect username or password' }
      }
    };
    axios.post.mockRejectedValue(mockErrorResponse);

    render(
      <AuthProvider>
        <Login />
      </AuthProvider>
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
      expect(screen.getByText(/incorrect username or password/i)).toBeInTheDocument();
    });
  });
});
