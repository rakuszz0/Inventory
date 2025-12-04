import React from 'react';
import { Alert } from 'react-bootstrap';
import { InventoryItem } from '../../types';

interface StockAlertProps {
  items: InventoryItem[];
}

const StockAlert: React.FC<StockAlertProps> = ({ items }) => {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <Alert variant="warning" className="mb-4">
      <Alert.Heading>Peringatan Stok Minimum!</Alert.Heading>
      <p>Beberapa barang mendekati atau sudah mencapai batas stok minimum:</p>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <strong>{item.name}</strong> - Stok: {item.current_stock} (Minimum: {item.min_stock || 10})
          </li>
        ))}
      </ul>
    </Alert>
  );
};

export default StockAlert;