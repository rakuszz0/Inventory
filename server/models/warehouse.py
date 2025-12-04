from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from server.core.database import Base

class Warehouse(Base):
    __tablename__ = "warehouses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    location = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship(
        "User",
        back_populates="warehouse",
        cascade="all, delete-orphan",
        foreign_keys="[User.warehouse_id]"
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by]
    )

    inventory_items = relationship(
        "InventoryItem",
        back_populates="warehouse",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_warehouse_code", "code"),
        Index("idx_warehouse_active", "is_active"),
        Index("idx_warehouse_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<Warehouse(id={self.id}, code={self.code}, name={self.name})>"
