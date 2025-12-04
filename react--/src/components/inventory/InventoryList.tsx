import React, { useState, useEffect } from 'react';
import { Table, Button, Badge, Form, Modal, Alert, Row, Col } from 'react-bootstrap';
import { useInventory } from '../../hooks/useInventory';
import { useAuth } from '../../hooks/useAuth';
import { formatCurrency } from '../../utils/helpers';
import { InventoryItem, InventoryFilters } from '../../types';
import InventoryForm from './InventoryForm';
import StockAlert from './StockAlert';

const InventoryList: React.FC = () => {
  const [showForm, setShowForm] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [currentItem, setCurrentItem] = useState<InventoryItem | null>(null);
  const [filters, setLocalFilters] = useState<InventoryFilters>({
    category_id: '',
    min_stock: 0,
    is_active: true,
  });
  const [searchTerm, setSearchTerm] = useState('');

  const {
    items,
    isLoading,
    error,
    pagination,
    filters: contextFilters,
    fetchItems,
    deleteItem,
    setFilters,
    setPagination,
    lowStockItems,
    categories,
    warehouses,
  } = useInventory();

  const { user } = useAuth();

  useEffect(() => {
    fetchItems(pagination.page, pagination.limit, { ...contextFilters, search: searchTerm });
  }, [pagination.page, pagination.limit, contextFilters, searchTerm]);

  const handleFilterChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ): void => {
    const target = e.target as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
    const key = target.name as keyof InventoryFilters;
    const rawValue = target.value;
    const parsedValue = key === 'min_stock' || key === 'max_stock' ? Number(rawValue) : rawValue;
    const newFilters = { ...filters, [key]: parsedValue } as InventoryFilters;
    setLocalFilters(newFilters);
    setFilters(newFilters);
    setPagination({ page: 1 });
  };

  const handleSearch = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ): void => {
    const target = e.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
    setSearchTerm((target as HTMLInputElement).value);
    setPagination({ page: 1 });
  };

  const handlePageChange = (page: number): void => {
    setPagination({ page });
  };

  const handleAddItem = (): void => {
    setCurrentItem(null);
    setShowForm(true);
  };

  const handleEditItem = (item: InventoryItem): void => {
    setCurrentItem(item);
    setShowForm(true);
  };

  const handleViewItem = (item: InventoryItem): void => {
    setCurrentItem(item);
    setShowViewModal(true);
  };

  const handleDeleteItem = (item: InventoryItem): void => {
    setCurrentItem(item);
    setShowDeleteModal(true);
  };

  const confirmDelete = async (): Promise<void> => {
    if (currentItem) {
      await deleteItem(currentItem.id);
      setShowDeleteModal(false);
      setCurrentItem(null);
    }
  };

  const isSuperAdmin = user?.role === 'super_admin';

  return (
    <div>
      <Row className="mb-4">
        <Col>
          <h2>Daftar Inventaris</h2>
        </Col>
        <Col className="text-end">
          <Button variant="primary" onClick={handleAddItem}>
            Tambah Barang
          </Button>
        </Col>
      </Row>

      {lowStockItems.length > 0 && <StockAlert items={lowStockItems} />}

      <Row className="mb-3">
        <Col md={3}>
          <Form.Group controlId="search">
            <Form.Control
              type="text"
              placeholder="Cari barang..."
              value={searchTerm}
              onChange={handleSearch}
            />
          </Form.Group>
        </Col>
        <Col md={2}>
          <Form.Group controlId="category_id">
            <Form.Select name="category_id" value={filters.category_id} onChange={handleFilterChange}>
              <option value="">Semua Kategori</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
        </Col>
        <Col md={2}>
          <Form.Group controlId="min_stock">
            <Form.Control
              type="number"
              placeholder="Stok Minimum"
              name="min_stock"
              value={filters.min_stock}
              onChange={handleFilterChange}
            />
          </Form.Group>
        </Col>
        <Col md={2}>
          <Form.Group controlId="max_stock">
            <Form.Control
              type="number"
              placeholder="Stok Maksimum"
              name="max_stock"
              value={filters.max_stock || ''}
              onChange={handleFilterChange}
            />
          </Form.Group>
        </Col>
        <Col md={3}>
          <Button
            variant="outline-secondary"
            onClick={() => {
              setLocalFilters({ category_id: '', min_stock: 0, max_stock: undefined, is_active: true });
              setFilters({ category_id: '', min_stock: 0, max_stock: undefined, is_active: true });
              setSearchTerm('');
            }}
          >
            Reset Filter
          </Button>
        </Col>
      </Row>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>No</th>
            <th>SKU</th>
            <th>Nama Barang</th>
            <th>Kategori</th>
            <th>Satuan</th>
            <th>Stok</th>
            <th>Harga Beli</th>
            <th>Harga Jual</th>
            <th>Nilai Inventaris</th>
            <th>Status</th>
            <th>Aksi</th>
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            <tr>
              <td colSpan={11} className="text-center">
                Memuat data...
              </td>
            </tr>
          ) : items.length === 0 ? (
            <tr>
              <td colSpan={11} className="text-center">
                Tidak ada data inventaris
              </td>
            </tr>
          ) : (
            items.map((item, index) => {
              const inventoryValue = item.current_stock * item.buy_price;
              const isLowStock = item.current_stock <= item.min_stock;

              return (
                <tr key={item.id}>
                  <td>{(pagination.page - 1) * pagination.limit + index + 1}</td>
                  <td>{item.sku}</td>
                  <td>{item.name}</td>
                  <td>{item.category_id}</td>
                  <td>{item.unit}</td>
                  <td>
                    {item.current_stock}
                    {isLowStock && (
                      <Badge bg="danger" className="ms-2">
                        Rendah
                      </Badge>
                    )}
                  </td>
                  <td>{formatCurrency(item.buy_price)}</td>
                  <td>{formatCurrency(item.sell_price)}</td>
                  <td>{formatCurrency(inventoryValue)}</td>
                  <td>
                    <Badge bg={item.is_active ? "success" : "secondary"}>
                      {item.is_active ? "Aktif" : "Tidak Aktif"}
                    </Badge>
                  </td>
                  <td>
                    <Button variant="info" size="sm" className="me-1" onClick={() => handleViewItem(item)}>
                      Lihat
                    </Button>
                    {(!isSuperAdmin || (isSuperAdmin && item.created_by === user?.id)) && (
                      <>
                        <Button variant="warning" size="sm" className="me-1" onClick={() => handleEditItem(item)}>
                          Edit
                        </Button>
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => handleDeleteItem(item)}
                          disabled={item.current_stock > 0}
                          title={item.current_stock > 0 ? 'Hanya barang dengan stok 0 yang dapat dihapus' : ''}
                        >
                          Hapus
                        </Button>
                      </>
                    )}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </Table>

      {pagination.totalPages > 1 && (
        <div className="d-flex justify-content-center mt-3">
          <Button
            variant="outline-primary"
            disabled={pagination.page === 1}
            onClick={() => handlePageChange(pagination.page - 1)}
          >
            Sebelumnya
          </Button>
          <span className="mx-3 align-self-center">
            Halaman {pagination.page} dari {pagination.totalPages}
          </span>
          <Button
            variant="outline-primary"
            disabled={pagination.page === pagination.totalPages}
            onClick={() => handlePageChange(pagination.page + 1)}
          >
            Selanjutnya
          </Button>
        </div>
      )}

      <InventoryForm show={showForm} handleClose={() => setShowForm(false)} item={currentItem} />

      <Modal show={showViewModal} onHide={() => setShowViewModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Detail Barang</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {currentItem && (
            <InventoryForm show={true} handleClose={() => setShowViewModal(false)} item={currentItem} isViewMode={true} />
          )}
        </Modal.Body>
      </Modal>

      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Konfirmasi Hapus</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Apakah Anda yakin ingin menghapus barang "{currentItem?.name}"?</p>
          <Alert variant="warning">Tindakan ini tidak dapat dibatalkan.</Alert>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Batal
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Hapus
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default InventoryList;