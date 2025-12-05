// --- Enums ---
export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  GUDANG: 'gudang',
  // Tambahkan role lain jika ada
  KASIR: 'kasir',
  MANAJER: 'manajer',
} as const;

export type UserRole = typeof ROLES[keyof typeof ROLES];

// --- User & Auth State ---
export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  warehouse_id?: string;
  is_active: boolean;
  is_verified?: boolean;
  created_at?: string;
  updated_at?: string;
  last_login?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// --- API Payloads & Requests ---
export interface LoginCredentials {
  username: string;
  password: string;
}

// Tipe ini untuk STATE form, termasuk field untuk validasi UI
export interface RegisterData {
  full_name: string;
  username: string;
  email: string;
  password: string;
  confirmPassword: string; // Hanya untuk validasi di frontend
  role: UserRole;
  warehouse_id?: string;
}

// Tipe ini untuk PAYLOAD yang dikirim ke backend API
export interface RegisterPayload {
  full_name: string;
  username: string;
  email: string;
  password: string;
  role: UserRole;
  warehouse_id?: string;
}

// --- API Responses ---
export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user?: User;
}

// --- Context Type ---
export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (userData: RegisterPayload) => Promise<void>; // Perbaikan: Gunakan RegisterPayload
  logout: () => void;
  clearError: () => void;
  hasRole: (role: UserRole) => boolean;
  hasAnyRole: (roles: UserRole[]) => boolean;
}