import React, {
  createContext,
  useContext,
  useReducer,
  useEffect,
  ReactNode,
  useCallback,
} from 'react';
import { inventoryService } from '../services/inventoryService';
import { toast } from 'react-toastify';

import {
  InventoryState,
  InventoryContextType,
  InventoryItem,
  InventoryFormData,
  InventoryFilters,
  Pagination,
  Category,
  Warehouse,
} from '../types';

const InventoryContext = createContext<InventoryContextType | undefined>(undefined);

const initialState: InventoryState = {
  items: [],
  categories: [],
  warehouses: [],
  lowStockItems: [],
  inventoryValue: 0,
  isLoading: false,
  error: null,
  filters: {
    category_id: '',
    min_stock: 0,
    search: '',
  },
  pagination: {
    page: 1,
    limit: 10,
    total: 0,
    totalPages: 0,
  },
};

type InventoryAction =
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; payload: { items: InventoryItem[]; pagination: Pagination } }
  | { type: 'FETCH_FAILURE'; payload: string }
  | { type: 'ADD_ITEM'; payload: InventoryItem }
  | { type: 'UPDATE_ITEM'; payload: InventoryItem }
  | { type: 'DELETE_ITEM'; payload: string }
  | { type: 'SET_CATEGORIES'; payload: Category[] }
  | { type: 'SET_WAREHOUSES'; payload: Warehouse[] }
  | { type: 'SET_LOW_STOCK_ITEMS'; payload: InventoryItem[] }
  | { type: 'SET_INVENTORY_VALUE'; payload: number }
  | { type: 'SET_FILTERS'; payload: Partial<InventoryFilters> }
  | { type: 'SET_PAGINATION'; payload: Partial<Pagination> }
  | { type: 'CLEAR_ERROR' }
  | { type: 'RESET_LOADING' };

const inventoryReducer = (state: InventoryState, action: InventoryAction): InventoryState => {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, isLoading: true, error: null };
    case 'FETCH_SUCCESS':
      return {
        ...state,
        isLoading: false,
        items: action.payload.items,
        pagination: action.payload.pagination,
        error: null,
      };
    case 'FETCH_FAILURE':
      return { ...state, isLoading: false, error: action.payload };
    case 'ADD_ITEM':
      return { ...state, items: [action.payload, ...state.items], isLoading: false, error: null };
    case 'UPDATE_ITEM':
      return {
        ...state,
        items: state.items.map((item) =>
          item.id === action.payload.id ? action.payload : item
        ),
        isLoading: false,
        error: null,
      };
    case 'DELETE_ITEM':
      return {
        ...state,
        items: state.items.filter((item) => item.id !== action.payload),
        isLoading: false,
        error: null,
      };
    case 'SET_CATEGORIES':
      return { ...state, categories: action.payload };
    case 'SET_WAREHOUSES':
      return { ...state, warehouses: action.payload };
    case 'SET_LOW_STOCK_ITEMS':
      return { ...state, lowStockItems: action.payload };
    case 'SET_INVENTORY_VALUE':
      return { ...state, inventoryValue: action.payload };
    case 'SET_FILTERS':
      return { ...state, filters: { ...state.filters, ...action.payload } };
    case 'SET_PAGINATION':
      return { ...state, pagination: { ...state.pagination, ...action.payload } };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    case 'RESET_LOADING':
      return { ...state, isLoading: false };
    default:
      return state;
  }
};

interface InventoryProviderProps {
  children: ReactNode;
}

export const InventoryProvider: React.FC<InventoryProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(inventoryReducer, initialState);

  // PERUBAHAN: Menggunakan 'inventory_token' untuk konsistensi dengan authService
  const token = typeof window !== 'undefined' ? localStorage.getItem('inventory_token') : null;

  // ============================
  // FETCH ITEMS
  // ============================
  const fetchItems = useCallback(
    async (page = 1, limit = 10, filters: Partial<InventoryFilters> = {}) => {
      if (!token) return;
      try {
        dispatch({ type: 'FETCH_START' });
        const params: InventoryFilters & { page: number; limit: number } = {
          page,
          limit,
          ...filters,
        };
        const res = await inventoryService.getAll(params);
        dispatch({ type: 'FETCH_SUCCESS', payload: { items: res.items, pagination: res.pagination } });
      } catch (err: any) {
        dispatch({ type: 'FETCH_FAILURE', payload: err.detail || err.message || 'Gagal mengambil data inventaris' });
      }
    },
    [token]
  );

  // ============================
  // ADD ITEM
  // ============================
  const addItem = useCallback(
    async (itemData: InventoryFormData): Promise<InventoryItem> => {
      try {
        dispatch({ type: 'FETCH_START' });
        const backendData = {
          name: itemData.name,
          category_id: itemData.category_id,
          current_stock: itemData.current_stock,
          min_stock: itemData.min_stock,
          max_stock: itemData.max_stock || 100,
          buy_price: itemData.buy_price,
          sell_price: itemData.sell_price,
          unit: itemData.unit || 'pcs',
          description: itemData.description || '',
          is_active: itemData.is_active ?? true,
          warehouse_id: itemData.warehouse_id, // <-- PERUBAHAN KRUSIAL DI SINI
        };
        const res = await inventoryService.create(backendData);
        dispatch({ type: 'ADD_ITEM', payload: res });
        toast.success('Barang berhasil ditambahkan');
        return res;
      } catch (err: any) {
        dispatch({ type: 'FETCH_FAILURE', payload: err.message || 'Gagal menambah barang' });
        toast.error(err.message || 'Gagal menambah barang');
        throw err;
      }
    },
    []
  );

  // ============================
  // UPDATE ITEM
  // ============================
  const updateItem = useCallback(
    async (id: string, itemData: Partial<InventoryFormData>): Promise<InventoryItem> => {
      try {
        dispatch({ type: 'FETCH_START' });
        const backendData: Partial<InventoryFormData> = {};
        Object.keys(itemData).forEach((key) => {
          const v: any = (itemData as any)[key];
          if (v !== undefined) backendData[key as keyof InventoryFormData] = v;
        });
        const res = await inventoryService.update(id, backendData);
        dispatch({ type: 'UPDATE_ITEM', payload: res });
        toast.success('Barang berhasil diperbarui');
        return res;
      } catch (err: any) {
        dispatch({ type: 'FETCH_FAILURE', payload: err.message || 'Gagal memperbarui barang' });
        toast.error(err.message || 'Gagal memperbarui barang');
        throw err;
      }
    },
    []
  );

  // ============================
  // DELETE ITEM
  // ============================
  const deleteItem = useCallback(async (id: string): Promise<void> => {
    try {
      dispatch({ type: 'FETCH_START' });
      await inventoryService.delete(id);
      dispatch({ type: 'DELETE_ITEM', payload: id });
      toast.success('Barang berhasil dihapus');
    } catch (err: any) {
      dispatch({ type: 'FETCH_FAILURE', payload: err.message || 'Gagal menghapus barang' });
      toast.error(err.message || 'Gagal menghapus barang');
      throw err;
    }
  }, []);

  // ============================
  // UPDATE STOCK
  // ============================
  const updateStock = useCallback(
    async (
      id: string,
      stockData: { stock: number; operation: 'add' | 'subtract' | 'set' }
    ): Promise<InventoryItem> => {
      try {
        dispatch({ type: 'FETCH_START' });

        const operationMap: Record<'add' | 'subtract' | 'set', 'in' | 'out' | 'adjustment'> = {
          add: 'in',
          subtract: 'out',
          set: 'adjustment',
        };

        const backendData = {
          quantity: stockData.operation === 'subtract' ? -stockData.stock : stockData.stock,
          transaction_type: operationMap[stockData.operation],
          reference: 'Manual adjustment',
          notes:
            stockData.operation === 'add'
              ? 'Menambah stok secara manual'
              : stockData.operation === 'subtract'
              ? 'Mengurangi stok secara manual'
              : 'Mengatur stok secara manual',
        };

        const res = await inventoryService.updateStock(id, backendData);
        dispatch({ type: 'UPDATE_ITEM', payload: res });
        toast.success('Stok berhasil diperbarui');
        return res;
      } catch (err: any) {
        dispatch({ type: 'FETCH_FAILURE', payload: err.message || 'Gagal memperbarui stok' });
        toast.error(err.message || 'Gagal memperbarui stok');
        throw err;
      }
    },
    []
  );

  // ============================
  // MOCK CATEGORIES
  // ============================
  const fetchCategories = useCallback(async (): Promise<void> => {
    const mockCategories: Category[] = [
      { id: '1', name: 'Elektronik' },
      { id: '2', name: 'Makanan' },
      { id: '3', name: 'Minuman' },
      { id: '4', name: 'Peralatan' },
      { id: '5', name: 'Lainnya' },
    ];
    dispatch({ type: 'SET_CATEGORIES', payload: mockCategories });
  }, []);

  // ============================
  // MOCK WAREHOUSES
  // ============================
  const fetchWarehouses = useCallback(async (): Promise<void> => {
    const mockWarehouses: Warehouse[] = [
      { id: '1', name: 'Gudang Utama', code: 'GDG-001' },
      { id: '2', name: 'Gudang Cabang', code: 'GDG-002' },
    ];
    dispatch({ type: 'SET_WAREHOUSES', payload: mockWarehouses });
  }, []);

  // ============================
  // FETCH LOW STOCK
  // ============================
  const fetchLowStockItems = useCallback(async (): Promise<void> => {
    if (!token) return;
    try {
      const res = await inventoryService.getLowStock();
      dispatch({ type: 'SET_LOW_STOCK_ITEMS', payload: res });
    } catch {}
  }, [token]);

  // ============================
  // FETCH INVENTORY VALUE
  // ============================
  const fetchInventoryValue = useCallback(async (): Promise<void> => {
    if (!token) return;
    try {
      const res = await inventoryService.getInventoryValue();
      dispatch({ type: 'SET_INVENTORY_VALUE', payload: res });
    } catch {}
  }, [token]);

  const setFilters = useCallback((filters: Partial<InventoryFilters>) => {
    dispatch({ type: 'SET_FILTERS', payload: filters });
  }, []);

  const setPagination = useCallback((pagination: Partial<Pagination>) => {
    dispatch({ type: 'SET_PAGINATION', payload: pagination });
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  // =====================================================
  // INITIAL LOAD
  // =====================================================
  useEffect(() => {
    if (!token) {
      console.log('Skip InventoryContext fetch — user belum login');
      return;
    }

    const loadInitialData = async () => {
      try {
        dispatch({ type: 'FETCH_START' });
        await Promise.all([
          fetchItems(),
          fetchCategories(),
          fetchWarehouses(),
          fetchLowStockItems(),
          fetchInventoryValue(),
        ]);
      } catch (err) {
        console.error('Gagal memuat data awal:', err);
      } finally {
        dispatch({ type: 'RESET_LOADING' });
      }
    };

    loadInitialData();
  }, [token, fetchItems, fetchCategories, fetchWarehouses, fetchLowStockItems, fetchInventoryValue]);

  const value: InventoryContextType = {
    ...state,
    fetchItems,
    addItem,
    updateItem,
    deleteItem,
    updateStock,
    fetchCategories,
    fetchWarehouses,
    fetchLowStockItems,
    fetchInventoryValue,
    setFilters,
    setPagination,
    clearError,
  };

  return <InventoryContext.Provider value={value}>{children}</InventoryContext.Provider>;
};

export const useInventory = (): InventoryContextType => {
  const context = useContext(InventoryContext);
  if (!context) {
    throw new Error('useInventory must be used within InventoryProvider');
  }
  return context;
};