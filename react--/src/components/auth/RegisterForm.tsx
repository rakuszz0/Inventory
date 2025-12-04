  import React, { useState, useEffect } from 'react';
  import { Form, Button, Card, Alert } from 'react-bootstrap';
  import { Link, useNavigate } from 'react-router-dom';
  import { useAuth } from '../../hooks/useAuth';
  import { ROLES } from '../../utils/constants';
  import { validateRegisterForm } from '../../utils/validation';
  import { RegisterData, RegisterFormData } from '../../types';

  const RegisterForm: React.FC = () => {
    const [formData, setFormData] = useState<RegisterFormData>({
      full_name: '',
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      role: ROLES.GUDANG,
      warehouse_id: '',
    });
    const [errors, setErrors] = useState<{ [key: string]: string }>({});
    const [isSubmitting, setIsSubmitting] = useState(false);

    const { register, error, isAuthenticated, clearError } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
      if (isAuthenticated) {
        navigate('/dashboard', { replace: true });
      }
    }, [isAuthenticated, navigate]);

    // Perbaiki tipe handleChange agar kompatibel dengan semua Form.Control
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
      const { name, value } = e.target;
      setFormData((prev) => ({ ...prev, [name]: value }));
      if (errors[name]) {
        setErrors((prev) => ({ ...prev, [name]: '' }));
      }
    };

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
      e.preventDefault();

      // Siapkan data untuk dikirim dengan tipe RegisterData
      const dataToSubmit: RegisterData = {
        full_name: formData.full_name,
        username: formData.username,
        email: formData.email,
        password: formData.password,
        confirmPassword: formData.confirmPassword,
        role: formData.role,
        // Hanya kirim warehouse_id jika role adalah 'gudang' dan fieldnya tidak kosong
        ...(formData.role === ROLES.GUDANG && formData.warehouse_id && { warehouse_id: formData.warehouse_id }),
      };
      
      // Validasi menggunakan RegisterFormData
      const formErrors = validateRegisterForm({ ...dataToSubmit, confirmPassword: formData.confirmPassword });
      if (Object.keys(formErrors).length > 0) {
        setErrors(formErrors);
        return;
      }

      setIsSubmitting(true);
      clearError();

      try {
        await register(dataToSubmit);
        navigate('/login');
      } catch (err) {
        console.error('Registration error:', err);
      } finally {
        setIsSubmitting(false);
      }
    };

    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '100vh' }}>
        <Card style={{ width: '450px' }}>
          <Card.Body>
            <Card.Title className="text-center mb-4">Registrasi</Card.Title>
            {error && <Alert variant="danger">{error}</Alert>}
            <Form onSubmit={handleSubmit}>
              <Form.Group className="mb-3" controlId="full_name">
                <Form.Label>Nama Lengkap</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="Masukkan nama lengkap"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  isInvalid={!!errors.full_name}
                />
                <Form.Control.Feedback type="invalid">{errors.full_name}</Form.Control.Feedback>
              </Form.Group>

              <Form.Group className="mb-3" controlId="username">
                <Form.Label>Username</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="Masukkan username"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  isInvalid={!!errors.username}
                />
                <Form.Control.Feedback type="invalid">{errors.username}</Form.Control.Feedback>
              </Form.Group>

              <Form.Group className="mb-3" controlId="email">
                <Form.Label>Email</Form.Label>
                <Form.Control
                  type="email"
                  placeholder="Masukkan email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  isInvalid={!!errors.email}
                />
                <Form.Control.Feedback type="invalid">{errors.email}</Form.Control.Feedback>
              </Form.Group>

              <Form.Group className="mb-3" controlId="password">
                <Form.Label>Password</Form.Label>
                <Form.Control
                  type="password"
                  placeholder="Masukkan password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  isInvalid={!!errors.password}
                />
                <Form.Control.Feedback type="invalid">{errors.password}</Form.Control.Feedback>
              </Form.Group>

              <Form.Group className="mb-3" controlId="confirmPassword">
                <Form.Label>Konfirmasi Password</Form.Label>
                <Form.Control
                  type="password"
                  placeholder="Konfirmasi password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  isInvalid={!!errors.confirmPassword}
                />
                <Form.Control.Feedback type="invalid">{errors.confirmPassword}</Form.Control.Feedback>
              </Form.Group>

              <Form.Group className="mb-3" controlId="role">
                <Form.Label>Role</Form.Label>
                <Form.Select
                  name="role"
                  value={formData.role}
                  onChange={(e) => handleChange(e as any)} // Type assertion untuk select
                  isInvalid={!!errors.role}
                >
                  <option value="">Pilih Role</option>
                  <option value={ROLES.GUDANG}>Gudang</option>
                  <option value={ROLES.SUPER_ADMIN}>Super Admin</option>
                </Form.Select>
                <Form.Control.Feedback type="invalid">{errors.role}</Form.Control.Feedback>
              </Form.Group>

              {/* Field Warehouse ID hanya muncul jika role adalah 'gudang' */}
              {formData.role === ROLES.GUDANG && (
                <Form.Group className="mb-3" controlId="warehouse_id">
                  <Form.Label>ID Gudang</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Masukkan ID Gudang (UUID)"
                    name="warehouse_id"
                    value={formData.warehouse_id}
                    onChange={handleChange}
                    isInvalid={!!errors.warehouse_id}
                  />
                  <Form.Control.Feedback type="invalid">{errors.warehouse_id}</Form.Control.Feedback>
                </Form.Group>
              )}

              <Button variant="primary" type="submit" className="w-100" disabled={isSubmitting}>
                {isSubmitting ? 'Memproses...' : 'Daftar'}
              </Button>
            </Form>

            <div className="text-center mt-3">
              <p>
                Sudah punya akun? <Link to="/login">Login</Link>
              </p>
            </div>
          </Card.Body>
        </Card>
      </div>
    );
  };

  export default RegisterForm;