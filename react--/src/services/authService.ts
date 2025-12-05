import axios from 'axios';
// Import SEMUA tipe dari file terpusat
import { LoginCredentials, RegisterPayload, User, AuthResponse } from '../types'; 

// Axios instance
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor untuk menambahkan Authorization header secara otomatis
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('inventory_token');
  if (token) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${token}`,
    };
  }
  return config;
});

// Tidak perlu mendefinisikan interface lagi di sini, karena sudah diimpor

class AuthService {
  private tokenKey = 'inventory_token';
  private refreshKey = 'refresh_token';
  private userKey = 'inventory_user';

  // Login user - Gunakan LoginCredentials
  async login(credentials: LoginCredentials): Promise<User> {
    try {
      const res = await api.post<AuthResponse>('/auth/login', credentials);
      const { access_token, refresh_token, user } = res.data;

      if (!access_token) throw new Error('Login failed: access token missing');

      this.setToken(access_token);
      if (refresh_token) localStorage.setItem(this.refreshKey, refresh_token);

      if (user) {
        this.setUser(user);
        return user;
      }

      const currentUser = await this.getCurrentUser();
      if (!currentUser) throw new Error('Login failed: user data missing');

      return currentUser;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async getCurrentUser(): Promise<User | null> {
    const token = this.getToken();
    if (!token) return null;

    try {
      const res = await api.get<User>('/auth/me');
      const user = res.data;
      if (user) this.setUser(user);
      return user || null;
    } catch (err) {
      console.error('Get current user error:', err);
      this.clearAuth();
      return null;
    }
  }

  // Register user - Gunakan RegisterPayload
  async register(data: RegisterPayload): Promise<void> {
    try {
      await api.post('/auth/register', data);
    } catch (error: any) {
      console.error('Register error:', error.response?.data || error.message);
      throw error;
    }
  }

  // Logout user
  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch (error: any) {
      console.error('Logout error:', error.response?.data || error.message);
    } finally {
      this.clearAuth();
      window.location.href = '/login';
    }
  }

  hasRole(role: string): boolean {
    const user = this.getUser();
    return user?.role === role;
  }

  hasAnyRole(roles: string[]): boolean {
    const user = this.getUser();
    return user ? roles.includes(user.role) : false;
  }

  // Simpan user ke localStorage
  setUser(user: User): void {
    localStorage.setItem(this.userKey, JSON.stringify(user));
  }

  // Ambil user dari localStorage
  getUser(): User | null {
    const userStr = localStorage.getItem(this.userKey);
    return userStr ? JSON.parse(userStr) : null;
  }

  // Auth helpers
  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  // LocalStorage helpers
  setToken(token: string): void {
    localStorage.setItem(this.tokenKey, token);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  clearAuth(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.refreshKey);
    localStorage.removeItem(this.userKey);
  }
}

export const authService = new AuthService();
export default api;