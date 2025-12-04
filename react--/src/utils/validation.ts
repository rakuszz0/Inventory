import { LoginCredentials, RegisterData, InventoryFormData } from '../types';

interface FormErrors {
  [key: string]: string;
}

export const validateLoginForm = (values: LoginCredentials): FormErrors => {
  const errors: FormErrors = {};
  
  if (!values.username || values.username.trim() === "") {
    errors.username = 'Username wajib diisi';
  }
  
  if (!values.password) {
    errors.password = 'Password wajib diisi';
  } else if (values.password.length < 6) {
    errors.password = 'Password minimal 6 karakter';
  }
  
  return errors;
};

export const validateRegisterForm = (values: RegisterData): FormErrors => {
  const errors: FormErrors = {};
  
  if (!values.full_name) {
    errors.full_name = 'Nama wajib diisi';
  }
  
  if (!values.username) {
    errors.username = 'Username wajib diisi';
  } else if (values.username.length < 3) {
    errors.username = 'Username tidak valid';
  }

  if (!values.email) {
    errors.email = 'Email wajib diisi';
  } else if (!/\S+@\S+\.\S+/.test(values.email)) {
    errors.email = 'Email tidak valid';
  }
  
  if (!values.password) {
    errors.password = 'Password wajib diisi';
  } else if (values.password.length < 6) {
    errors.password = 'Password minimal 6 karakter';
  }
  
  if (!values.confirmPassword) {
    errors.confirmPassword = 'Konfirmasi password wajib diisi';
  } else if (values.password !== values.confirmPassword) {
    errors.confirmPassword = 'Password tidak cocok';
  }
  
  if (!values.role) {
    errors.role = 'Role wajib dipilih';
  }
  
  return errors;
};

export const validateInventoryForm = (values: InventoryFormData): FormErrors => {
  const errors: FormErrors = {};
  
  if (!values.name || values.name.trim() === "") {
    errors.name = 'Nama barang wajib diisi';
  }
  
  if (!values.category_id) {
    errors.category_id = 'Kategori wajib dipilih';
  }
  
  if (!values.unit || values.unit.trim() === "") {
    errors.unit = 'Satuan wajib diisi';
  }
  
  // Validasi stok
  if (values.current_stock === undefined || values.current_stock === null) {
    errors.current_stock = 'Stok wajib diisi';
  } else if (typeof values.current_stock !== 'number' || isNaN(values.current_stock) || values.current_stock < 0) {
    errors.current_stock = 'Stok tidak boleh negatif';
  }
  
  // Validasi stok minimum
  if (values.min_stock === undefined || values.min_stock === null) {
    errors.min_stock = 'Stok minimum wajib diisi';
  } else if (typeof values.min_stock !== 'number' || isNaN(values.min_stock) || values.min_stock < 0) {
    errors.min_stock = 'Stok minimum tidak boleh negatif';
  }
  
  // Validasi stok maksimum (opsional)
  if (values.max_stock !== undefined && values.max_stock !== null) {
    if (typeof values.max_stock !== 'number' || isNaN(values.max_stock) || values.max_stock < 0) {
      errors.max_stock = 'Stok maksimum tidak boleh negatif';
    } else if (values.max_stock < values.min_stock) {
      errors.max_stock = 'Stok maksimum harus lebih besar dari stok minimum';
    }
  }
  
  // Validasi harga beli
  if (values.buy_price === undefined || values.buy_price === null) {
    errors.buy_price = 'Harga beli wajib diisi';
  } else if (typeof values.buy_price !== 'number' || isNaN(values.buy_price) || values.buy_price <= 0) {
    errors.buy_price = 'Harga beli harus lebih dari 0';
  }
  
  // Validasi harga jual
  if (values.sell_price === undefined || values.sell_price === null) {
    errors.sell_price = 'Harga jual wajib diisi';
  } else if (typeof values.sell_price !== 'number' || isNaN(values.sell_price) || values.sell_price <= 0) {
    errors.sell_price = 'Harga jual harus lebih dari 0';
  } else if (values.sell_price <= values.buy_price) {
    errors.sell_price = 'Harga jual harus lebih tinggi dari harga beli';
  }
  
  return errors;
};