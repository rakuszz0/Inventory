# models/inventory.py

from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Text, Boolean, Numeric, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from decimal import Decimal

from server.core.database import Base

# Impor model yang diperlukan untuk relasi
from server.models.warehouse import Warehouse
from server.models.user import User
from server.models.category import Category  # <-- Tambahkan impor ini

# HAPUS KELAS CATEGORY YANG ADA DI SINI
# class Category(Base): ...

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    barcode = Column(String(100), unique=True, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"))
    unit = Column(String(50), default="pcs")
    current_stock = Column(Integer, default=0, nullable=False)
    min_stock = Column(Integer, default=10, nullable=False)
    max_stock = Column(Integer, nullable=True)
    buy_price = Column(Numeric(15, 2), nullable=False)
    sell_price = Column(Numeric(15, 2), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relasi akan berfungsi dengan benar karena Category sekarang diimpor
    category = relationship("Category", back_populates="inventory_items")
    warehouse = relationship("Warehouse", back_populates="inventory_items")
    creator = relationship("User", back_populates="inventory_items")
    transactions = relationship("Transaction", back_populates="item", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('current_stock >= 0', name='check_stock_non_negative'),
        CheckConstraint('sell_price >= 0', name='check_sell_price_non_negative'),
        CheckConstraint('buy_price >= 0', name='check_buy_price_non_negative'),
        CheckConstraint('min_stock >= 0', name='check_min_stock_non_negative'),
        Index("idx_item_warehouse_category", "warehouse_id", "category_id"),
    )
    
    @property
    def total_value(self) -> Decimal:
        return self.current_stock * self.buy_price
    
    @property
    def profit_margin(self) -> Decimal:
        if self.buy_price > 0:
            return ((self.sell_price - self.buy_price) / self.buy_price) * 100
        return Decimal('0')
    
    @property
    def stock_status(self) -> str:
        if self.current_stock == 0:
            return "out_of_stock"
        elif self.current_stock <= self.min_stock:
            return "low_stock"
        elif self.max_stock and self.current_stock >= self.max_stock:
            return "over_stock"
        else:
            return "normal"
