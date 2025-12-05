import React, { createContext, useState, useEffect, ReactNode } from 'react';
// Import SEMUA tipe dari '../types', JANGAN dari authService
import { 
  User, 
  LoginCredentials, 
  RegisterPayload, // Gunakan RegisterPayload
  AuthContextType 
} from '../types'; 
// Import instance authService, bukan tipenya
import { authService } from '../services/authService';

// AuthContextType sudah diimpor, tidak perlu didefinisikan ulang
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

      // PERBAIKAN: authService.login membutuhkan satu objek, bukan dua argumen terpisah
      const loggedInUser = await authService.login(credentials);

      if (loggedInUser) {
        setUser(loggedInUser);
        // Catatan: Menggunakan useNavigate dari react-router-dom lebih disarankan daripada window.location.href
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

  // PERBAIKAN: Gunakan RegisterPayload untuk tipe parameter
  const register = async (data: RegisterPayload) => {
    try {
      setLoading(true);
      setError(null);
      await authService.register(data);
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

  const value: AuthContextType = {
    user,
    token: null,
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