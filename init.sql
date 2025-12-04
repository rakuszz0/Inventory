-- init.sql
-- Initialization script for Inventory Management System
-- Run this script after database creation

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================
-- 1. INSERT DEFAULT WAREHOUSE
-- ==============================================
INSERT INTO warehouses (
    id, name, code, location, address, 
    phone, email, is_active, created_at
) VALUES (
    uuid_generate_v4(),
    'Gudang Utama',
    'WH-001',
    'Jakarta Pusat',
    'Jl. Sudirman No. 123, Jakarta 10220',
    '021-12345678',
    'gudang@inventory.com',
    TRUE,
    NOW()
) ON CONFLICT (code) DO NOTHING;

-- ==============================================
-- 2. INSERT DEFAULT CATEGORIES
-- ==============================================
INSERT INTO categories (id, name, description, is_active, created_at) VALUES
    (uuid_generate_v4(), 'Elektronik', 'Barang elektronik dan gadget', TRUE, NOW()),
    (uuid_generate_v4(), 'Pakaian', 'Pakaian dan aksesoris', TRUE, NOW()),
    (uuid_generate_v4(), 'Makanan & Minuman', 'Makanan dan minuman', TRUE, NOW()),
    (uuid_generate_v4(), 'Alat Tulis', 'Alat tulis kantor', TRUE, NOW()),
    (uuid_generate_v4(), 'Perlengkapan Rumah', 'Peralatan rumah tangga', TRUE, NOW())
ON CONFLICT (name) DO NOTHING;


-- ==============================================
-- 4. INSERT WAREHOUSE STAFF USER
-- ==============================================
-- Password: Staff123! (bcrypt hash)
WITH warehouse_id AS (
    SELECT id FROM warehouses WHERE code = 'WH-001' LIMIT 1
)
INSERT INTO users (
    id, email, username, full_name, password_hash,
    role, warehouse_id, is_active, is_verified, created_at
) SELECT
    uuid_generate_v4(),
    'staff@gudang.com',
    'staff_gudang',
    'Staff Gudang',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'gudang',
    warehouse_id.id,
    TRUE,
    TRUE,
    NOW()
FROM warehouse_id
ON CONFLICT (email) DO NOTHING;

-- ==============================================
-- 5. INSERT SAMPLE INVENTORY ITEMS
-- ==============================================
WITH 
    warehouse_id AS (SELECT id FROM warehouses WHERE code = 'WH-001' LIMIT 1),
    category_id AS (SELECT id FROM categories WHERE name = 'Elektronik' LIMIT 1),
    admin_id AS (SELECT id FROM users WHERE username = 'admin' LIMIT 1)
INSERT INTO inventory_items (
    id, sku, name, description, category_id, warehouse_id,
    unit, current_stock, min_stock, max_stock,
    buy_price, sell_price, is_active, created_by, created_at
) SELECT
    uuid_generate_v4(),
    'ELEC-001',
    'Laptop Dell XPS 13',
    'Laptop premium dengan processor Intel i7',
    category_id.id,
    warehouse_id.id,
    'pcs',
    15,
    5,
    50,
    15000000.00,
    18000000.00,
    TRUE,
    admin_id.id,
    NOW()
FROM warehouse_id, category_id, admin_id
ON CONFLICT (sku) DO NOTHING;

WITH 
    warehouse_id AS (SELECT id FROM warehouses WHERE code = 'WH-001' LIMIT 1),
    category_id AS (SELECT id FROM categories WHERE name = 'Pakaian' LIMIT 1),
    admin_id AS (SELECT id FROM users WHERE username = 'admin' LIMIT 1)
INSERT INTO inventory_items (
    id, sku, name, description, category_id, warehouse_id,
    unit, current_stock, min_stock, max_stock,
    buy_price, sell_price, is_active, created_by, created_at
) SELECT
    uuid_generate_v4(),
    'PAKAIAN-001',
    'Kaos Polo T-Shirt',
    'Kaos polo bahan katun premium',
    category_id.id,
    warehouse_id.id,
    'pcs',
    100,
    20,
    500,
    75000.00,
    120000.00,
    TRUE,
    admin_id.id,
    NOW()
FROM warehouse_id, category_id, admin_id
ON CONFLICT (sku) DO NOTHING;

-- ==============================================
-- 6. CREATE INDEXES FOR BETTER PERFORMANCE
-- ==============================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_warehouse ON users(warehouse_id);

CREATE INDEX IF NOT EXISTS idx_inventory_items_sku ON inventory_items(sku);
CREATE INDEX IF NOT EXISTS idx_inventory_items_barcode ON inventory_items(barcode);
CREATE INDEX IF NOT EXISTS idx_inventory_items_warehouse_category ON inventory_items(warehouse_id, category_id);

CREATE INDEX IF NOT EXISTS idx_transactions_item_date ON transactions(item_id, created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_code ON transactions(transaction_code);

CREATE INDEX IF NOT EXISTS idx_stock_alerts_unread ON stock_alerts(is_read, created_at);

-- ==============================================
-- 7. UPDATE SEQUENCES (if using serial IDs)
-- ==============================================
-- Note: Not needed for UUID primary keys

-- ==============================================
-- 8. PRINT SUCCESS MESSAGE
-- ==============================================
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully!';
    RAISE NOTICE 'Default admin user: admin@inventory.com / Admin123!';
    RAISE NOTICE 'Default warehouse staff: staff@gudang.com / Staff123!';
    RAISE NOTICE 'Warehouse: Gudang Utama (WH-001)';
END $$;