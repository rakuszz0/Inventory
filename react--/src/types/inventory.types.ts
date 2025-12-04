export interface InventoryItem {
  id: string; // Ubah dari _id ke id untuk konsistensi
  name: string;
  category_id: string;
  category?: Category; // Gunakan interface Category
  current_stock: number;
  min_stock: number;
  max_stock?: number;
  buy_price: number;
  sell_price: number;
  unit: string;
  sku: string;
  description?: string;
  warehouse_id?: string;
  warehouse?: Warehouse; // Gunakan interface Warehouse
  created_by: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface InventoryFormData {
  name: string;
  category_id: string;
  current_stock: number;
  min_stock: number;
  max_stock?: number;
  buy_price: number;
  sell_price: number;
  warehouse_id?: string;
  unit: string;
  description?: string;
  is_active?: boolean; // Tambahkan ini
}

export interface Category {
  id: string;
  name: string;
  description?: string;
  is_active?: boolean;
}

export interface Warehouse {
  id: string;
  name: string;
  code?: string;
  address?: string;
  phone?: string;
  is_active?: boolean;
}

export interface InventoryFilters {
  category_id?: string;
  min_stock?: number;
  max_stock?: number;
  search?: string;
  warehouse_id?: string;
  is_active?: boolean;
}

export interface Pagination {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: Pagination;
}

export interface InventoryState {
  items: InventoryItem[];
  categories: Category[]; // Gunakan Category[]
  warehouses: Warehouse[]; // Tambahkan warehouses
  lowStockItems: InventoryItem[];
  inventoryValue: number;
  isLoading: boolean;
  error: string | null;
  filters: InventoryFilters;
  pagination: Pagination;
}

export interface InventoryContextType extends InventoryState {
  fetchItems: (page?: number, limit?: number, filters?: InventoryFilters) => Promise<void>;
  addItem: (itemData: InventoryFormData) => Promise<InventoryItem>;
  updateItem: (id: string, itemData: Partial<InventoryFormData>) => Promise<InventoryItem>;
  deleteItem: (id: string) => Promise<void>;
  updateStock: (id: string, stockData: { stock: number; operation: 'add' | 'subtract' | 'set' }) => Promise<InventoryItem>;
  fetchCategories: () => Promise<void>;
  fetchWarehouses: () => Promise<void>; // Tambahkan ini
  fetchLowStockItems: () => Promise<void>;
  fetchInventoryValue: () => Promise<void>;
  setFilters: (filters: Partial<InventoryFilters>) => void;
  setPagination: (pagination: Partial<Pagination>) => void;
  clearError: () => void;
}