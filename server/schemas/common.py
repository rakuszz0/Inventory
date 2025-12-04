from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 100
    
    @classmethod
    def from_query(cls, skip: int = 0, limit: int = 100):
        return cls(skip=skip, limit=limit)

class FilterParams(BaseModel):
    is_active: Optional[bool] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None

class SearchParams(BaseModel):
    search: Optional[str] = None
    fields: Optional[List[str]] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    skip: int
    limit: int
    has_more: bool
    
    @classmethod
    def from_items(cls, items: List[Any], total: int, skip: int, limit: int):
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total
        )

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HealthCheckResponse(BaseModel):
    status: str
    database: bool = False
    redis: bool = False
    uptime: float
    timestamp: datetime = datetime.now()
    
    class Config:
        from_attributes = True