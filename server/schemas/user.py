from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

# =========================
# Enum Roles
# =========================
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    GUDANG = "gudang"

# =========================
# Base Models
# =========================
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole
    warehouse_id: Optional[UUID] = None

# =========================
# Create & Update Models
# =========================
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

    warehouse_id: Optional[UUID] = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

    @validator('warehouse_id')
    def validate_warehouse_for_gudang(cls, v, values):
        if 'role' in values and values['role'] == UserRole.GUDANG and not v:
            raise ValueError('Warehouse staff must be assigned to a warehouse')
        if 'role' in values and values['role'] == UserRole.SUPER_ADMIN and v:
            raise ValueError('Super admin cannot be assigned to a warehouse')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    warehouse_id: Optional[UUID] = None

    @validator('warehouse_id')
    def validate_warehouse_update(cls, v, values):
        if 'role' in values and values['role'] == UserRole.SUPER_ADMIN and v:
            raise ValueError('Super admin cannot be assigned to a warehouse')
        return v

# =========================
# DB Models
# =========================
class UserInDB(UserBase):
    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# =========================
# Response Models
# =========================
class UserResponse(UserInDB):
    warehouse: Optional['WarehouseResponse'] = None  # Forward reference

    class Config:
        from_attributes = True

class UserDetailResponse(UserResponse):
    total_created_items: int = 0
    total_transactions: int = 0

    class Config:
        from_attributes = True


# =========================
# Login Response
# =========================
class UserLoginResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    full_name: str
    role: UserRole
    warehouse_id: Optional[UUID] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# =========================
# Auth / Token Models
# =========================
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    sub: str  # user ID
    email: str
    role: UserRole
    warehouse_id: Optional[UUID] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

# =========================
# User Stats
# =========================
class UserStatsResponse(BaseModel):
    user_id: UUID
    total_items_created: int
    total_transactions: int
    last_activity: Optional[datetime] = None
    average_transactions_per_day: float = 0.0

    class Config:
        from_attributes = True

# =========================
# Rebuild forward references (Pydantic 2.x fix)
# =========================
from server.schemas.warehouse import WarehouseResponse  # pastikan ini ada
UserResponse.model_rebuild()
UserDetailResponse.model_rebuild()
UserCreate.model_rebuild()
UserUpdate.model_rebuild()
UserInDB.model_rebuild()
Token.model_rebuild()
TokenData.model_rebuild()
LoginRequest.model_rebuild()
RefreshTokenRequest.model_rebuild()
ChangePasswordRequest.model_rebuild()
UserStatsResponse.model_rebuild()
UserLoginResponse.model_rebuild()
