import api from './api';
import {
InventoryItem,
InventoryFormData,
InventoryFilters,
PaginatedResponse,
} from '../types';

interface StockUpdateData {
quantity: number;
transaction_type: 'in' | 'out' | 'adjustment';
reference?: string;
notes?: string;
}

export const inventoryService = {
getAll: async (params?: {
page?: number;
limit?: number;
category_id?: string;
min_stock?: number;
max_stock?: number;
search?: string;
warehouse_id?: string;
is_active?: boolean;
}): Promise<PaginatedResponse<InventoryItem>> => {
const response = await api.get('/inventory', { params });
return response.data as PaginatedResponse<InventoryItem>;
},

create: async (data: InventoryFormData): Promise<InventoryItem> => {
const response = await api.post('/inventory', data);
return response.data as InventoryItem;
},

update: async (id: string, data: Partial<InventoryFormData>): Promise<InventoryItem> => {
const response = await api.put(`/inventory/${id}`, data);
return response.data as InventoryItem;
},

delete: async (id: string): Promise<void> => {
await api.delete(`/inventory/${id}`);
},

updateStock: async (id: string, data: StockUpdateData): Promise<InventoryItem> => {
const response = await api.post(`/inventory/${id}/stock`, data);
return response.data as InventoryItem;
},

getLowStock: async (): Promise<InventoryItem[]> => {
const response = await api.get('/inventory/low-stock');
return response.data as InventoryItem[];
},

getInventoryValue: async (): Promise<number> => {
const response = await api.get('/inventory/value');
return response.data as number;
},
};
