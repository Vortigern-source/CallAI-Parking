const API_BASE_URL = '/api/v1';

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('token');
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  async handleResponse(response) {
    if (response.status === 401) {
      this.setToken(null);
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      throw new Error('Incorrect username or password');
    }

    if (!response.ok) {
      let errorMessage;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || JSON.stringify(errorData);
      } catch (e) {
        errorMessage = `HTTP error! status: ${response.status}`;
      }
      throw new Error(errorMessage);
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    return response.text();
  }

  async get(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse(response);
  }

  async post(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(data),
    });

    return this.handleResponse(response);
  }

  async put(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(data),
    });

    return this.handleResponse(response);
  }

  async delete(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse(response);
  }

  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username.trim());
    formData.append('password', password.trim());

    try {
      const response = await fetch(`${API_BASE_URL}/auth/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
        credentials: 'include',
      });

      const data = await this.handleResponse(response);
      if (data.access_token) {
        this.setToken(data.access_token);
        return data;
      } else {
        throw new Error('No access token received');
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async me() {
    return this.get('/auth/me');
  }

  async getDashboardStats() {
    return this.get('/dashboard');
  }

  async getBookings(params = {}) {
    const queryParams = new URLSearchParams(params).toString();
    const url = queryParams ? `/bookings?${queryParams}` : '/bookings';
    return this.get(url);
  }

  async getUserSettings() {
    return this.get('/settings');
  }

  async updateUserSettings(settings) {
    return this.put('/settings', settings);
  }

  async getGlobalSettings() {
    return this.get('/settings/global');
  }

  async updateGlobalSettings(settings) {
    return this.put('/settings/global', settings);
  }

  async getBotConfig() {
    return this.get('/bot/config');
  }

  async updateBotConfig(config) {
    return this.put('/bot/config', config);
  }

  // Admin User Management Methods
  async listUsers() {
    return this.get('/admin/users');
  }

  async createUser(userData) {
    return this.post('/admin/create-user', userData);
  }

  async updateUser(username, userData) {
    return this.put(`/admin/update-user/${username}`, userData);
  }

  async deleteUser(username) {
    return this.delete(`/admin/delete-user/${username}`);
  }
}

export const api = new ApiClient();