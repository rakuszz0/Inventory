import axios from 'axios';

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

export interface LoginData {
  username: string;
  password: string;
}

export interface RegisterData {
  full_name: string;
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  role: 'super_admin' | 'gudang' | 'kasir' | 'manajer';
  warehouse_id?: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: 'super_admin' | 'gudang' | 'kasir' | 'manajer';
  warehouse_id?: string;
  is_active: boolean;
  is_verified?: boolean;
  created_at?: string;
  updated_at?: string;
  last_login?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user?: User;
}

class AuthService {
  private tokenKey = 'inventory_token';
  private refreshKey = 'refresh_token';
  private userKey = 'inventory_user';

  // Login user
  async login(username: string, password: string): Promise<User> {
    try {
      const res = await api.post<AuthResponse>('/auth/login', { username, password });
      const { access_token, refresh_token, user } = res.data;

      if (!access_token) throw new Error('Login failed: access token missing');

      this.setToken(access_token);
      if (refresh_token) localStorage.setItem(this.refreshKey, refresh_token);

      // Jika user data sudah ada di respons login, gunakan itu
      if (user) {
        this.setUser(user);
        return user;
      }

      // Jika tidak, ambil user setelah login
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
      // Perbaikan: respons dari /auth/me adalah user langsung, bukan { user: ... }
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

  // Register user
  async register(data: RegisterData): Promise<AuthResponse> {
    try {
      const response = await api.post<AuthResponse>('/auth/register', data);
      return response.data;
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