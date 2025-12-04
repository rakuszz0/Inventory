from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text, Numeric, CheckConstraint, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from enum import Enum as PyEnum
from server.core.database import Base

class TransactionType(str, PyEnum):
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    TRANSFER = "transfer"

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_code = Column(String(50), unique=True, nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=True)
    total_price = Column(Numeric(15, 2), nullable=True)
    previous_stock = Column(Integer, nullable=False)
    new_stock = Column(Integer, nullable=False)
    reference = Column(String(100), nullable=True)
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    item = relationship("InventoryItem", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
    
    __table_args__ = (
        CheckConstraint('quantity != 0', name='check_quantity_not_zero'),
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        Index("idx_transaction_item_date", "item_id", "created_at"),
        Index("idx_transaction_code", "transaction_code"),
    )

class StockAlert(Base):
    __tablename__ = "stock_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False)
    alert_type = Column(String(20), nullable=False)
    current_stock = Column(Integer, nullable=False)
    threshold = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    read_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    item = relationship("InventoryItem")
    reader = relationship("User", foreign_keys=[read_by])
    
    __table_args__ = (
        Index("idx_alert_unread", "is_read", "created_at"),
        Index("idx_alert_item", "item_id", "created_at"),
    )
