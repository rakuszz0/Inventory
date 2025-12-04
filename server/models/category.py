# models/category.py

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Index, CheckConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from server.core.database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    slug = Column(String(255), unique=True, nullable=True, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Self-referential relationship for parent-child hierarchy
    parent = relationship(
        "Category",
        remote_side=[id],
        back_populates="subcategories",
        foreign_keys=[parent_id]
    )
    subcategories = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_id]
    )
    
    # Relationship to inventory items
    inventory_items = relationship("InventoryItem", back_populates="category", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_category_name", "name"),
        Index("idx_category_parent", "parent_id"),
        Index("idx_category_active", "is_active"),
        Index("idx_category_slug", "slug"),
        Index("idx_category_sort", "sort_order"),
        CheckConstraint('parent_id != id', name='check_no_self_parent'),
    )
    
    # --- PERBAIKAN KRUSIAL: Buat __repr__ sangat aman ---
    # JANGAN PERNAH MENGAKSES ATTRIBUT SELAIN 'id'
    # Ini mencegah DetachedInstanceError saat error handling
    def __repr__(self):
        return f"<Category(id={self.id})>"
    
    def to_dict(self):
        """Convert category to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def full_path(self):
        """Get full category path (e.g., Electronics > Computers > Laptops)"""
        path = []
        current = self
        
        while current:
            path.insert(0, current.name)
            current = current.parent
        
        return " > ".join(path)
    
    @property
    def level(self):
        """Get category level in hierarchy (0 = root)"""
        level = 0
        current = self.parent
        
        while current:
            level += 1
            current = current.parent
        
        return level
    
    @classmethod
    def generate_slug(cls, name):
        """Generate slug from category name"""
        import re
        slug = name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug

class CategoryHistory(Base):
    """Track changes to category data"""
    __tablename__ = "category_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    field_name = Column(String(50), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    category = relationship("Category")
    changer = relationship("User")
    
    __table_args__ = (
        Index("idx_chistory_category", "category_id"),
        Index("idx_chistory_date", "changed_at"),
    )
    
    # --- PERBAIKAN KRUSIAL: Buat __repr__ sangat aman ---
    def __repr__(self):
        return f"<CategoryHistory(id={self.id})>"