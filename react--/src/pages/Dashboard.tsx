import React, { useEffect } from 'react';
import { Row, Col, Card, Badge } from 'react-bootstrap';
import { useInventory } from '../hooks/useInventory';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency } from '../utils/helpers';

const Dashboard: React.FC = () => {
  const { items, inventoryValue, lowStockItems, fetchItems, fetchLowStockItems, fetchInventoryValue } = useInventory();
  const { user } = useAuth();

  useEffect(() => {
    fetchItems();
    fetchLowStockItems();
    fetchInventoryValue();
  }, [fetchItems, fetchLowStockItems, fetchInventoryValue]);

  const totalItems = items.length;
  const totalStock = items.reduce((sum, item) => sum + item.current_stock, 0);
  const lowStockCount = lowStockItems.length;

  return (
    <div>
      <h2 className="mb-4">Dashboard</h2>
      <p>Selamat datang, {user?.full_name}!</p>

      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Total Jenis Barang</Card.Title>
              <h2>{totalItems}</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Total Stok</Card.Title>
              <h2>{totalStock}</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Nilai Inventaris</Card.Title>
              <h2>{formatCurrency(inventoryValue)}</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Stok Minimum</Card.Title>
              <h2>
                {lowStockCount}
                {lowStockCount > 0 && (
                  <Badge bg="danger" className="ms-2">
                    Peringatan
                  </Badge>
                )}
              </h2>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row>
        <Col md={6}>
          <Card>
            <Card.Header>Barang dengan Stok Minimum</Card.Header>
            <Card.Body>
              {lowStockItems.length === 0 ? (
                <p>Tidak ada barang dengan stok minimum.</p>
              ) : (
                <ul>
                  {lowStockItems.map((item) => (
                    <li key={item.id}>
                      {item.name} - Stok: {item.current_stock} (Minimum: {item.min_stock || 10})
                    </li>
                  ))}
                </ul>
              )}
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Header>Kategori Barang</Card.Header>
            <Card.Body>
              <p>Grafik kategori barang akan ditampilkan di sini.</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;