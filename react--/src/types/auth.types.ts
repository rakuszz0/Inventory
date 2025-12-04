export interface User {
  id: string;
  full_name: string;
  email: string;
  role: 'super_admin' | 'gudang';
  createdAt: string;
  updatedAt: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData extends LoginCredentials {
  full_name: string;
  email: string;
  username: string;
  confirmPassword: string;
  role: 'super_admin' | 'gudang';
  warehouse_id?: string;
}

export interface RegisterFormData extends RegisterData {
  confirmPassword: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<User>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}