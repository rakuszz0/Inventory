from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import re


class WarehouseBase(BaseModel):
    """Base warehouse schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Warehouse name")
    code: str = Field(..., min_length=1, max_length=50, description="Unique warehouse code")
    location: Optional[str] = Field(None, description="Location/area")
    address: Optional[str] = Field(None, description="Full address")
    phone: Optional[str] = Field(None, description="Contact phone")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    
    @validator('code')
    def validate_code_format(cls, v):
        """Validate warehouse code format"""
        if not re.match(r'^[A-Z0-9_-]+$', v):
            raise ValueError('Warehouse code must contain only uppercase letters, numbers, hyphens, and underscores')
        return v.upper()  # Always store as uppercase
    
    @validator('phone')
    def validate_phone_format(cls, v):
        """Validate phone number format"""
        if v and not re.match(r'^[\d\s\-\+\(\)]+$', v):
            raise ValueError('Invalid phone number format')
        return v


class WarehouseCreate(WarehouseBase):
    """Schema for creating a warehouse"""
    pass


class WarehouseUpdate(BaseModel):
    """Schema for updating a warehouse"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    location: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    
    @validator('code')
    def validate_code_update(cls, v):
        if v:
            if not re.match(r'^[A-Z0-9_-]+$', v):
                raise ValueError('Warehouse code must contain only uppercase letters, numbers, hyphens, and underscores')
            return v.upper()
        return v


class WarehouseInDB(WarehouseBase):
    """Warehouse schema as stored in database"""
    id: UUID
    is_active: bool = True
    created_by: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class WarehouseResponse(WarehouseInDB):
    """Warehouse response schema"""
    pass


class WarehouseDetailResponse(WarehouseResponse):
    """Warehouse with additional details"""
    total_items: int = 0
    total_stock: int = 0
    total_value: float = 0.0
    low_stock_items: int = 0
    out_of_stock_items: int = 0
    total_users: int = 0
    
    class Config:
        from_attributes = True


class WarehouseWithStats(WarehouseResponse):
    """Warehouse with inventory statistics"""
    inventory_summary: dict = {}
    recent_transactions: List[dict] = []
    top_items: List[dict] = []
    
    class Config:
        from_attributes = True


class WarehouseBulkCreate(BaseModel):
    """Schema for bulk warehouse creation"""
    warehouses: List[WarehouseCreate]


class WarehouseBulkUpdate(BaseModel):
    """Schema for bulk warehouse update"""
    warehouse_ids: List[UUID]
    update_data: WarehouseUpdate


class WarehouseTransferRequest(BaseModel):
    """Schema for transferring items between warehouses"""
    from_warehouse_id: UUID
    to_warehouse_id: UUID
    items: List[dict]  # List of {item_id: UUID, quantity: int}
    notes: Optional[str] = None
    
    @validator('to_warehouse_id')
    def validate_different_warehouses(cls, v, values):
        if 'from_warehouse_id' in values and v == values['from_warehouse_id']:
            raise ValueError('Cannot transfer to the same warehouse')
        return v


class WarehouseSearchParams(BaseModel):
    """Parameters for warehouse search"""
    search: Optional[str] = None
    is_active: Optional[bool] = True
    location: Optional[str] = None
    skip: int = 0
    limit: int = 100