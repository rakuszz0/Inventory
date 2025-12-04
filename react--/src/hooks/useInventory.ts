import { useInventory as useInventoryContext } from '../context/InventoryContext';

export const useInventory = () => {
  return useInventoryContext();
};