import React, { useState, useEffect } from 'react';
import { Form, Button, Modal, Alert } from 'react-bootstrap';
import { useInventory } from '../../hooks/useInventory';
import { validateInventoryForm } from '../../utils/validation';
import { formatCurrency } from '../../utils/helpers';
import { InventoryItem, InventoryFormData } from '../../types';

interface InventoryFormProps {
  show: boolean;
  handleClose: () => void;
  item?: InventoryItem | null;
  isViewMode?: boolean;
}

const InventoryForm: React.FC<InventoryFormProps> = ({ show, handleClose, item = null, isViewMode = false }) => {
  const { categories, addItem, updateItem } = useInventory();
  const [formData, setFormData] = useState<InventoryFormData>({
    name: '',
    description: '',
    category_id: '',
    unit: 'pcs',
    current_stock: 0,
    min_stock: 5,
    max_stock: 1000,
    buy_price: 0,
    sell_price: 0,
    is_active: true,
  });
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (item) {
      setFormData({
        name: item.name || '',
        description: item.description || '',
        category_id: item.category_id || '',
        unit: item.unit || 'pcs',
        current_stock: item.current_stock || 0,
        min_stock: item.min_stock || 5,
        max_stock: item.max_stock || 1000,
        buy_price: item.buy_price || 0,
        sell_price: item.sell_price || 0,
        is_active: item.is_active !== undefined ? item.is_active : true,
      });
    } else {
      setFormData({
        name: '',
        description: '',
        category_id: '',
        unit: 'pcs',
        current_stock: 0,
        min_stock: 5,
        max_stock: 1000,
        buy_price: 0,
        sell_price: 0,
        is_active: true,
      });
    }
    setErrors({});
  }, [item, show]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>): void => {
    const target = e.target as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
    const { name, value, type } = target;
    
    let processedValue: any = value;
    
    if (type === 'number') {
      processedValue = value === '' ? 0 : parseFloat(value);
      if (isNaN(processedValue)) processedValue = 0;
    } else if (type === 'checkbox') {
      processedValue = (target as HTMLInputElement).checked;
    }
    
    setFormData((prev) => ({ ...prev, [name]: processedValue }));
    
    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    
    // Filter out undefined values for validation
    const validationData: InventoryFormData = {
      ...formData,
      description: formData.description || undefined,
      max_stock: formData.max_stock || undefined,
    };
    
    const formErrors = validateInventoryForm(validationData);
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      return;
    }

    setIsSubmitting(true);

    try {
      if (item) {
        // Untuk update, kirim semua data termasuk is_active
        await updateItem(item.id, formData);
      } else {
        // Untuk create, kirim semua data termasuk is_active
        await addItem(formData);
      }
      handleClose();
    } catch (err: any) {
      console.error('Form submission error:', err);
      setErrors({ submit: err.message || 'Gagal menyimpan data. Silakan coba lagi.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal show={show} onHide={handleClose} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>
          {isViewMode ? 'Detail Barang' : item ? 'Edit Barang' : 'Tambah Barang'}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {errors.submit && (
          <Alert variant="danger" className="mb-3">
            {errors.submit}
          </Alert>
        )}
        
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3" controlId="name">
            <Form.Label>Nama Barang</Form.Label>
            <Form.Control
              type="text"
              placeholder="Masukkan nama barang"
              name="name"
              value={formData.name}
              onChange={handleChange}
              disabled={isViewMode}
              isInvalid={!!errors.name}
            />
            <Form.Control.Feedback type="invalid">{errors.name}</Form.Control.Feedback>
          </Form.Group>

          <Form.Group className="mb-3" controlId="description">
            <Form.Label>Deskripsi</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              placeholder="Masukkan deskripsi barang"
              name="description"
              value={formData.description || ''}
              onChange={handleChange}
              disabled={isViewMode}
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="category_id">
            <Form.Label>Kategori</Form.Label>
            <Form.Select
              name="category_id"
              value={formData.category_id}
              onChange={handleChange}
              disabled={isViewMode}
              isInvalid={!!errors.category_id}
            >
              <option value="">Pilih Kategori</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">{errors.category_id}</Form.Control.Feedback>
          </Form.Group>

          <Form.Group className="mb-3" controlId="unit">
            <Form.Label>Satuan</Form.Label>
            <Form.Control
              type="text"
              placeholder="Masukkan satuan (pcs, kg, dll)"
              name="unit"
              value={formData.unit}
              onChange={handleChange}
              disabled={isViewMode}
              isInvalid={!!errors.unit}
            />
            <Form.Control.Feedback type="invalid">{errors.unit}</Form.Control.Feedback>
          </Form.Group>

          <div className="row">
            <div className="col-md-4">
              <Form.Group className="mb-3" controlId="current_stock">
                <Form.Label>Stok Saat Ini</Form.Label>
                <Form.Control
                  type="number"
                  min="0"
                  placeholder="Masukkan jumlah stok"
                  name="current_stock"
                  value={formData.current_stock}
                  onChange={handleChange}
                  disabled={isViewMode}
                  isInvalid={!!errors.current_stock}
                />
                <Form.Control.Feedback type="invalid">{errors.current_stock}</Form.Control.Feedback>
              </Form.Group>
            </div>
            
            <div className="col-md-4">
              <Form.Group className="mb-3" controlId="min_stock">
                <Form.Label>Stok Minimum</Form.Label>
                <Form.Control
                  type="number"
                  min="0"
                  placeholder="Masukkan stok minimum"
                  name="min_stock"
                  value={formData.min_stock}
                  onChange={handleChange}
                  disabled={isViewMode}
                  isInvalid={!!errors.min_stock}
                />
                <Form.Control.Feedback type="invalid">{errors.min_stock}</Form.Control.Feedback>
              </Form.Group>
            </div>
            
            <div className="col-md-4">
              <Form.Group className="mb-3" controlId="max_stock">
                <Form.Label>Stok Maksimum (Opsional)</Form.Label>
                <Form.Control
                  type="number"
                  min="0"
                  placeholder="Masukkan stok maksimum"
                  name="max_stock"
                  value={formData.max_stock}
                  onChange={handleChange}
                  disabled={isViewMode}
                  isInvalid={!!errors.max_stock}
                />
                <Form.Control.Feedback type="invalid">{errors.max_stock}</Form.Control.Feedback>
              </Form.Group>
            </div>
          </div>

          <div className="row">
            <div className="col-md-6">
              <Form.Group className="mb-3" controlId="buy_price">
                <Form.Label>Harga Beli</Form.Label>
                <Form.Control
                  type="number"
                  min="0"
                  step="100"
                  placeholder="Masukkan harga beli"
                  name="buy_price"
                  value={formData.buy_price}
                  onChange={handleChange}
                  disabled={isViewMode}
                  isInvalid={!!errors.buy_price}
                />
                <Form.Control.Feedback type="invalid">{errors.buy_price}</Form.Control.Feedback>
                {formData.buy_price > 0 && (
                  <Form.Text className="text-muted">{formatCurrency(formData.buy_price)}</Form.Text>
                )}
              </Form.Group>
            </div>
            
            <div className="col-md-6">
              <Form.Group className="mb-3" controlId="sell_price">
                <Form.Label>Harga Jual</Form.Label>
                <Form.Control
                  type="number"
                  min="0"
                  step="100"
                  placeholder="Masukkan harga jual"
                  name="sell_price"
                  value={formData.sell_price}
                  onChange={handleChange}
                  disabled={isViewMode}
                  isInvalid={!!errors.sell_price}
                />
                <Form.Control.Feedback type="invalid">{errors.sell_price}</Form.Control.Feedback>
                {formData.sell_price > 0 && (
                  <Form.Text className="text-muted">{formatCurrency(formData.sell_price)}</Form.Text>
                )}
              </Form.Group>
            </div>
          </div>

          {!isViewMode && (
            <Form.Group className="mb-3" controlId="is_active">
              <Form.Check
                type="checkbox"
                label="Aktif"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
              />
            </Form.Group>
          )}

          {formData.buy_price > 0 && formData.sell_price > 0 && (
            <Alert variant="info">
              <strong>Margin:</strong> {formatCurrency(formData.sell_price - formData.buy_price)} (
              {((formData.sell_price - formData.buy_price) / formData.buy_price * 100).toFixed(2)}%)
            </Alert>
          )}

          {!isViewMode && (
            <div className="d-flex justify-content-end">
              <Button variant="secondary" onClick={handleClose} className="me-2">
                Batal
              </Button>
              <Button variant="primary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Memproses...' : item ? 'Perbarui' : 'Simpan'}
              </Button>
            </div>
          )}
        </Form>
      </Modal.Body>
      {isViewMode && (
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Tutup
          </Button>
        </Modal.Footer>
      )}
    </Modal>
  );
};

export default InventoryForm;