# schemas/inventory.py

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum

# Impor schema yang diperlukan untuk relasi
from server.schemas.user import UserBase
from server.schemas.category import CategoryResponse
from server.schemas.warehouse import WarehouseResponse

# Definisi Enum yang mungkin diperlukan
class TransactionType(str, Enum):
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    TRANSFER = "transfer"

# ==================
# INVENTORY ITEM SCHEMAS
# ==================

class InventoryItemBase(BaseModel):
    """Base inventory item schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category_id: UUID
    warehouse_id: Optional[UUID] = None
    unit: str = "pcs"
    current_stock: int = 0
    min_stock: int = 10
    max_stock: Optional[int] = None
    buy_price: Decimal
    sell_price: Decimal
    is_active: bool = True

class InventoryItemCreate(InventoryItemBase):
    """Schema for creating an inventory item"""
    pass

class InventoryItemUpdate(BaseModel):
    """Schema for updating an inventory item"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[UUID] = None
    unit: Optional[str] = None
    current_stock: Optional[int] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None
    buy_price: Optional[Decimal] = None
    sell_price: Optional[Decimal] = None
    is_active: Optional[bool] = None

class InventoryItemInDB(InventoryItemBase):
    """Inventory item schema as stored in database"""
    id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# SCHEMA YANG HILANG - TAMBAHKAN INI
class InventoryItemResponse(InventoryItemInDB):
    """Inventory item response schema"""
    category: Optional[CategoryResponse] = None
    warehouse: Optional[WarehouseResponse] = None
    creator: Optional[UserBase] = None
    
    class Config:
        from_attributes = True

class InventoryItemDetailResponse(InventoryItemResponse):
    """Inventory item with detailed information"""
    transactions: List['TransactionResponse'] = []
    stock_status: str
    total_value: Decimal
    
    class Config:
        from_attributes = True

class PaginatedInventoryResponse(BaseModel):
    """Paginated response for inventory items"""
    items: List[InventoryItemResponse]
    pagination: dict

# ==================
# STOCK ADJUSTMENT SCHEMAS
# ==================

class StockAdjustmentRequest(BaseModel):
    """Schema for stock adjustment requests"""
    transaction_type: TransactionType
    quantity: int = Field(..., gt=0)
    reference: Optional[str] = None
    notes: Optional[str] = None

# ==================
# TRANSACTION SCHEMAS
# ==================

class TransactionBase(BaseModel):
    item_id: UUID
    transaction_type: TransactionType
    quantity: int = Field(..., gt=0)
    unit_price: Optional[Decimal] = None
    reference: Optional[str] = None
    notes: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    reference: Optional[str] = None
    notes: Optional[str] = None

class TransactionResponse(TransactionBase):
    id: UUID
    transaction_code: str
    total_price: Optional[Decimal] = None
    previous_stock: int
    new_stock: int
    created_by: UUID
    created_at: datetime
    
    # Relationship fields (optional)
    item: Optional['InventoryItemResponse'] = None
    user: Optional[UserBase] = None
    
    class Config:
        from_attributes = True

class TransactionDetailResponse(TransactionResponse):
    """Transaction with all relationships"""
    item: Optional['InventoryItemResponse'] = None
    user: Optional[UserBase] = None
    
    class Config:
        from_attributes = True

# ==================
# STOCK ALERT SCHEMAS
# ==================

class StockAlertBase(BaseModel):
    alert_type: str = Field(..., pattern="^(low_stock|out_of_stock|over_stock)$")
    message: Optional[str] = None

class StockAlertCreate(StockAlertBase):
    item_id: UUID
    current_stock: int
    threshold: int

class StockAlertUpdate(BaseModel):
    is_read: Optional[bool] = None

class StockAlertResponse(BaseModel):
    id: UUID
    item_id: UUID
    item_name: str
    alert_type: str
    current_stock: int
    threshold: int
    message: str
    is_read: bool
    read_by: Optional[UUID] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================
# REPORT SCHEMAS
# ==================

class DailySalesSummary(BaseModel):
    date: datetime
    transaction_count: int
    total_quantity: int
    total_sales: Decimal
    unique_items: int

class SalesReportResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_transactions: int
    total_quantity: int
    total_sales: Decimal
    average_daily_sales: Decimal
    daily_sales: List[DailySalesSummary]
    
    class Config:
        from_attributes = True

class StockMovement(BaseModel):
    date: datetime
    closing_stock: int
    stock_in: int
    stock_out: int

class StockMovementResponse(BaseModel):
    item_id: UUID
    period_days: int
    start_date: datetime
    end_date: datetime
    movement: List[StockMovement]
    
    class Config:
        from_attributes = True

# ==================
# INVENTORY SUMMARY SCHEMAS
# ==================

class InventoryValueResponse(BaseModel):
    """Response for inventory value endpoint"""
    value: float
    currency: str = "IDR"
    warehouse_id: Optional[UUID] = None

class InventorySummary(BaseModel):
    """Inventory summary statistics"""
    total_items: int
    total_stock: int
    total_value: float
    out_of_stock_items: int
    low_stock_items: int
    categories_summary: List[dict] = []

# Rebuild forward references
TransactionResponse.model_rebuild()
TransactionDetailResponse.model_rebuild()
InventoryItemDetailResponse.model_rebuild()