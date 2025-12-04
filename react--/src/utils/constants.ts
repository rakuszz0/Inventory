export const API_BASE_URL: string = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  GUDANG: 'gudang',
} as const;

export type Role = typeof ROLES[keyof typeof ROLES];

export const CATEGORIES: string[] = [
  'Elektronik',
  'Pakaian',
  'Makanan',
  'Minuman',
  'Peralatan Rumah Tangga',
  'Kosmetik',
  'Obat-obatan',
  'Lainnya',
];

export const STOCK_ALERT_THRESHOLD: number = 10;