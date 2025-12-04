import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { authService, User, RegisterData } from '../services/authService';
import { LoginCredentials } from '../types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  error: string | null;
  clearError: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
      setError(null);
    } catch (err) {
      console.error('Auth check error:', err);
      setUser(null);
      setError('Not authenticated');
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials: LoginCredentials) => {
  try {
    setLoading(true);
    setError(null);

    const loggedInUser = await authService.login(credentials.username, credentials.password);

    if (loggedInUser) {
      setUser(loggedInUser);

      // Redirect sesuai role
      switch (loggedInUser.role) {
        case 'super_admin':
          window.location.href = '/dashboard/superadmin';
          break;
        case 'gudang':
          window.location.href = '/dashboard/gudang';
          break;
        default:
          window.location.href = '/';
      }
    } else {
      setError('Login failed: user data missing');
    }

  } catch (err: any) {
    setError(err?.message || 'Login failed');
    throw err;
  } finally {
    setLoading(false);
  }
};


  const register = async (data: RegisterData) => {
  try {
    setLoading(true);
    setError(null);
    await authService.register(data);
    // Bisa langsung login otomatis atau redirect, tergantung kebutuhan
  } catch (err: any) {
    setError(err?.message || 'Registration failed');
    throw err;
  } finally {
    setLoading(false);
  }
};


  const logout = async () => {
    await authService.logout();
    setUser(null);
    setError(null);
  };

  const clearError = () => setError(null);

  const isAuthenticated = !!user;
  const hasRole = (role: string) => authService.hasRole(role);
  const hasAnyRole = (roles: string[]) => authService.hasAnyRole(roles);

  const value = {
    user,
    isLoading,
    login,
    register,
    logout,
    isAuthenticated,
    hasRole,
    hasAnyRole,
    error,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
