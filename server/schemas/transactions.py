from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum
from server.schemas.inventory import InventoryItemResponse
from server.schemas.user import UserBase


class TransactionType(str, Enum):
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    TRANSFER = "transfer"

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
    user: Optional['UserBase'] = None
    
    class Config:
        from_attributes = True

class TransactionDetailResponse(TransactionResponse):
    """Transaction with all relationships"""
    item: Optional['InventoryItemResponse'] = None
    user: Optional['UserBase'] = None
    
    class Config:
        from_attributes = True

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

TransactionResponse.model_rebuild()
TransactionDetailResponse.model_rebuild()
