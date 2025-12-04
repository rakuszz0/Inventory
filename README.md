# InventortApp

Inventory Management System dengan FastAPI (Backend) dan React.js + TypeScript (Frontend)

## ✨ Fitur Utama

### Backend (FastAPI)
- ✅ **Autentikasi JWT** - Register, Login, Refresh Token, Logout
- ✅ **Role-based Access Control (RBAC)** - Super Admin & Gudang Staff
- ✅ **Manajemen Password** - Ganti password dengan validasi
- ✅ **CRUD Lengkap** - Kategori & Inventory dengan validasi
- ✅ **Hierarki Kategori** - Parent-child relationship dengan validasi
- ✅ **Middleware Audit** - Logging semua request dan error
- ✅ **Database PostgreSQL** - SQLAlchemy Async dengan relationship
- ✅ **Dokumentasi API Otomatis** - Swagger UI & ReDoc
- ✅ **CORS Enabled** - Untuk integrasi dengan frontend

### Frontend (React.js + TypeScript)
- ✅ **Autentikasi Lengkap** - Login, Register, Protected Routes
- ✅ **Dashboard Responsif** - Statistik inventory real-time
- ✅ **Manajemen Inventory** - CRUD dengan validasi form
- ✅ **Sistem Kategori** - Hierarki kategori yang terstruktur
- ✅ **Stock Alert** - Notifikasi stok hampir habis
- ✅ **Pencarian & Filter** - Cari inventory berdasarkan nama/kategori
- ✅ **Context API** - State management terpusat
- ✅ **Type Safety** - TypeScript untuk kode yang lebih aman
- ✅ **UI/UX Modern** - Layout responsif dengan sidebar

## 📁 Struktur Project

```
InventortApp/
├── server/                          # Backend FastAPI
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py
│   │       │   ├── categories.py
│   │       │   ├── inventory.py
│   │       │   └── users.py
│   │       └── __init__.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── dependencies.py
│   ├── models/
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── inventory.py
│   │   └── audit_log.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── category.py
│   │   ├── inventory.py
│   │   └── user.py
│   ├── middleware/
│   │   └── audit_middleware.py
│   ├── utils/
│   │   ├── validators.py
│   │   └── helpers.py
│   ├── main.py
│   └── requirements.txt
├── react--/                          # Frontend React
│   ├── public/
│   │   ├── index.html
│   │   ├── vite.svg
│   │   └── favicon.ico
│   ├── src/
│   │   ├── assets/
│   │   │   ├── images/
│   │   │   ├── styles/
│   │   │   │   └── globals.css
│   │   │   └── icons/
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   └── RegisterForm.tsx
│   │   │   ├── common/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Loading.tsx
│   │   │   │   ├── ProtectedRoute.tsx
│   │   │   │   └── Sidebar.tsx
│   │   │   ├── inventory/
│   │   │   │   ├── InventoryForm.tsx
│   │   │   │   ├── InventoryList.tsx
│   │   │   │   └── StockAlert.tsx
│   │   │   ├── categories/
│   │   │   │   ├── CategoryForm.tsx
│   │   │   │   └── CategoryTree.tsx
│   │   │   └── layout/
│   │   │       └── MainLayout.tsx
│   │   ├── context/
│   │   │   ├── AuthContext.tsx
│   │   │   └── InventoryContext.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useInventory.ts
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Inventory.tsx
│   │   │   ├── Categories.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   └── Profile.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── authService.ts
│   │   │   └── inventoryService.ts
│   │   ├── types/
│   │   │   ├── auth.types.ts
│   │   │   ├── inventory.types.ts
│   │   │   ├── category.types.ts
│   │   │   └── index.ts
│   │   ├── utils/
│   │   │   ├── constants.ts
│   │   │   ├── helpers.ts
│   │   │   └── validation.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── routes.tsx
│   │   └── vite-env.d.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── README.md
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 🚀 Cara Menjalankan

### Prasyarat
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- npm atau yarn

### 1. Setup Backend

```bash
# Clone repository (jika ada)
git clone <repository-url>
cd InventortApp/server

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env file dengan konfigurasi database Anda

# Jalankan migrasi database (jika menggunakan Alembic)
alembic upgrade head

# Jalankan server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Setup Frontend

```bash
cd ../client

# Install dependencies
npm install

# Setup environment variables
cp .env.example .env
# Edit .env file dengan URL API backend

# Jalankan development server
npm run dev

# Atau untuk build production
npm run build
npm run preview
```

### 3. Menggunakan Docker (Opsional)

```bash
# Build dan jalankan semua services
docker-compose up -d

# Hanya backend
docker-compose up backend -d

# Hanya frontend
docker-compose up frontend -d
```

## ⚙️ Konfigurasi Environment Variables

### Backend (.env di folder server)
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/inventortdb

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# App
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Admin Default
DEFAULT_ADMIN_EMAIL=admin@inventort.com
DEFAULT_ADMIN_PASSWORD=Admin123!
```

### Frontend (.env di folder client)
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=InventortApp
VITE_APP_VERSION=1.0.0
```

## 🔗 API Endpoints

### Autentikasi
- `POST /api/v1/auth/register` - Register user baru
- `POST /api/v1/auth/login` - Login dan dapatkan token
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/change-password` - Ganti password

### User Management
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update profile
- `GET /api/v1/users/` - Get all users (Admin only)
- `PUT /api/v1/users/{user_id}/role` - Update user role (Admin only)

### Categories
- `GET /api/v1/categories/` - Get all categories
- `GET /api/v1/categories/{category_id}` - Get category detail
- `POST /api/v1/categories/` - Create new category
- `PUT /api/v1/categories/{category_id}` - Update category
- `DELETE /api/v1/categories/{category_id}` - Delete category
- `GET /api/v1/categories/tree/` - Get category tree

### Inventory
- `GET /api/v1/inventory/` - Get all inventory items
- `GET /api/v1/inventory/{item_id}` - Get item detail
- `POST /api/v1/inventory/` - Create new item
- `PUT /api/v1/inventory/{item_id}` - Update item
- `DELETE /api/v1/inventory/{item_id}` - Delete item
- `GET /api/v1/inventory/low-stock/` - Get low stock alerts
- `GET /api/v1/inventory/statistics/` - Get inventory statistics

## 👥 Roles & Permissions

### Super Admin
- ✅ Full access semua fitur
- ✅ Manage users dan roles
- ✅ CRUD semua data
- ✅ View audit logs

### Gudang Staff
- ✅ CRUD inventory items
- ✅ View categories
- ✅ View low stock alerts
- ❌ Tidak bisa manage users
- ❌ Tidak bisa delete categories

## 📊 Fitur Dashboard

1. **Ringkasan Statistik**
   - Total items in inventory
   - Total categories
   - Low stock items
   - Recent activities

2. **Inventory Management**
   - Add/Edit/Delete items
   - Bulk operations
   - Import/Export (CSV)
   - Barcode generation

3. **Category Management**
   - Hierarchical categories
   - Drag & drop organization
   - Bulk category assignment

4. **Reporting**
   - Stock level reports
   - Activity logs
   - User activity tracking

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Pastikan PostgreSQL berjalan
   sudo service postgresql start
   
   # Cek koneksi
   psql -h localhost -U user -d inventortdb
   ```

2. **Port Already in Use**
   ```bash
   # Cek process yang menggunakan port
   sudo lsof -i :8000
   sudo lsof -i :3000
   
   # Kill process
   kill -9 <PID>
   ```

3. **Module Not Found Error**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt
   npm install
   ```

## 🧪 Testing

### Backend Testing
```bash
cd server
pytest tests/ -v
```

### Frontend Testing
```bash
cd client
npm test
```

### API Testing dengan curl
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

## 📈 Deployment

### Backend (Production)
```bash
# Gunakan gunicorn untuk production
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Atau dengan Docker
docker build -f docker/Dockerfile.backend -t inventort-backend .
docker run -p 8000:8000 --env-file .env inventort-backend
```

### Frontend (Production)
```bash
cd client
npm run build
# File static akan dihasilkan di folder dist/
```

## 🤝 Kontribusi

1. Fork repository
2. Buat feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

## 📄 License

MIT License - lihat [LICENSE](LICENSE) file untuk detail.

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [React.js](https://reactjs.org/) - UI library
- [PostgreSQL](https://www.postgresql.org/) - Database
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework

## 📞 Support

Untuk masalah dan pertanyaan:
1. Cek [Issues](https://github.com/rakuszz0/Inventory)
2. Buat issue baru
3. Email: ilahir66@gmail.com

---

**InventortApp** © 2025 - Sistem Manajemen Inventory Modern