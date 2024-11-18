import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import { AuthProvider } from '../src/context/AuthContext';
import AdminManagement from '../src/pages/AdminManagement';

// Mock axios
jest.mock('axios');

// Mock AuthContext for admin user
const mockAdminUser = {
  user: {
    username: 'admin',
    role: 'admin',
    token: 'fake_admin_token'
  }
};
jest.mock('../src/context/AuthContext', () => ({
  ...jest.requireActual('../src/context/AuthContext'),
  useAuth: () => mockAdminUser
}));

describe('Admin Management Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders admin management page for admin users', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <AdminManagement />
        </AuthProvider>
      </BrowserRouter>
    );

    // Check page title
    expect(screen.getByText(/Admin User Management/i)).toBeInTheDocument();
    
    // Check form elements
    expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
  });

  test('creates new admin user', async () => {
    // Mock successful user creation
    const mockCreateUserResponse = {
      data: {
        message: 'Admin user created successfully',
        username: 'newadmin'
      }
    };
    axios.post.mockResolvedValue(mockCreateUserResponse);

    // Mock list of users
    const mockUsersResponse = {
      data: [
        { id: 1, username: 'existingadmin', email: 'existing@example.com' }
      ]
    };
    axios.get.mockResolvedValue(mockUsersResponse);

    render(
      <BrowserRouter>
        <AuthProvider>
          <AdminManagement />
        </AuthProvider>
      </BrowserRouter>
    );

    // Fill out new user form
    fireEvent.change(screen.getByLabelText(/Username/i), { 
      target: { value: 'newadmin' } 
    });
    fireEvent.change(screen.getByLabelText(/Email/i), { 
      target: { value: 'newadmin@example.com' } 
    });
    fireEvent.change(screen.getByLabelText(/Password/i), { 
      target: { value: 'SecurePassword123!' } 
    });

    // Submit form
    fireEvent.click(screen.getByText(/Create Admin User/i));

    // Wait for API calls
    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        '/api/admin/create-user', 
        expect.objectContaining({
          username: 'newadmin',
          email: 'newadmin@example.com'
        }),
        expect.any(Object)
      );
    });
  });

  test('deletes admin user', async () => {
    // Mock list of users
    const mockUsersResponse = {
      data: [
        { id: 1, username: 'admin1', email: 'admin1@example.com' },
        { id: 2, username: 'admin2', email: 'admin2@example.com' }
      ]
    };
    axios.get.mockResolvedValue(mockUsersResponse);

    // Mock delete user response
    const mockDeleteResponse = {
      data: {
        message: 'Admin user deleted successfully',
        username: 'admin2'
      }
    };
    axios.delete.mockResolvedValue(mockDeleteResponse);

    render(
      <BrowserRouter>
        <AuthProvider>
          <AdminManagement />
        </AuthProvider>
      </BrowserRouter>
    );

    // Wait for users to load
    await waitFor(() => {
      expect(screen.getByText(/admin1/i)).toBeInTheDocument();
      expect(screen.getByText(/admin2/i)).toBeInTheDocument();
    });

    // Find and click delete button for admin2
    const deleteButtons = screen.getAllByText(/Delete/i);
    fireEvent.click(deleteButtons[1]);

    // Wait for delete API call
    await waitFor(() => {
      expect(axios.delete).toHaveBeenCalledWith(
        '/api/admin/users/2',
        expect.any(Object)
      );
    });
  });

  test('prevents access for non-admin users', () => {
    // Mock non-admin user
    jest.mock('../src/context/AuthContext', () => ({
      ...jest.requireActual('../src/context/AuthContext'),
      useAuth: () => ({
        user: {
          username: 'regularuser',
          role: 'client'
        }
      })
    }));

    render(
      <BrowserRouter>
        <AuthProvider>
          <AdminManagement />
        </AuthProvider>
      </BrowserRouter>
    );

    // Check for access denied message
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
