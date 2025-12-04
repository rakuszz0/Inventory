from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    parent_id: Optional[UUID] = Field(None)
    slug: Optional[str] = Field(None, description="URL-friendly identifier")


class CategoryCreate(CategoryBase):
    """Schema for creating a category"""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    
    @validator('parent_id')
    def validate_parent_id(cls, v, values):
        """Prevent circular reference"""
        # This would be validated in the API layer
        return v


class CategoryInDB(CategoryBase):
    """Category schema as stored in database"""
    id: UUID
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


class CategoryResponse(CategoryInDB):
    """Category response schema"""
    parent: Optional['CategoryResponse'] = None
    subcategories: List['CategoryResponse'] = []
    
    class Config:
        from_attributes = True


class CategoryTreeResponse(BaseModel):
    """Category tree response for hierarchy view"""
    id: UUID
    name: str
    description: Optional[str]
    level: int = 0
    children: List['CategoryTreeResponse'] = []
    
    class Config:
        from_attributes = True


class CategoryWithStats(CategoryResponse):
    """Category with inventory statistics"""
    total_items: int = 0
    total_stock: int = 0
    total_value: float = 0.0
    low_stock_items: int = 0
    out_of_stock_items: int = 0
    
    class Config:
        from_attributes = True


class CategoryBulkCreate(BaseModel):
    """Schema for bulk category creation"""
    categories: List[CategoryCreate]


class CategoryBulkUpdate(BaseModel):
    """Schema for bulk category update"""
    category_ids: List[UUID]
    update_data: CategoryUpdate

class CategoryDetailResponse(CategoryResponse):
    """Category with detailed info"""
    class Config:
        from_attributes = True



# Handle forward reference
CategoryDetailResponse.model_rebuild()
CategoryResponse.update_forward_refs()
CategoryTreeResponse.update_forward_refs()