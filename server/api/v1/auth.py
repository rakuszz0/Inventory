from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from server.schemas.user import UserLoginResponse


from server import crud, schemas
from server.api.v1 import deps
from server.core import security
from server.core.config import settings

router = APIRouter(tags=["authentication"])

# ============================================================
# REGISTER (JSON ONLY)
# ============================================================
@router.post("/register", response_model=schemas.UserResponse)
async def register(
    body: schemas.UserCreate,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Register user dengan JSON body.
    Contoh payload:
    {
        "email": "user@example.com",
        "username": "user123",
        "password": "Password123",
        "full_name": "John Doe",
        "role": "gudang",
        "warehouse_id": "123e4567-e89b-12d3-a456-426614174000"
    }
    """
    # Check email & username
    if await crud.user.get_by_email(db, email=body.email):
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    if await crud.user.get_by_username(db, username=body.username):
        raise HTTPException(status_code=400, detail="Username already registered.")

    # Validasi warehouse untuk role gudang
    if body.role == schemas.UserRole.GUDANG and not body.warehouse_id:
        raise HTTPException(
            status_code=400, 
            detail="Warehouse staff must be assigned to a warehouse"
        )

    # Validasi warehouse untuk super_admin
    if body.role == schemas.UserRole.SUPER_ADMIN and body.warehouse_id:
        raise HTTPException(
            status_code=400,
            detail="Super admin cannot be assigned to a warehouse"
        )

    # Cek warehouse exists jika ada warehouse_id
    if body.warehouse_id:
        warehouse = await crud.warehouse.get(db, id=body.warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=400, detail="Warehouse not found")

    user = await crud.user.create(db, obj_in=body)
    return user


# ============================================================
# LOGIN (JSON ONLY)
# ============================================================
@router.post("/login", response_model=schemas.Token)
async def login(
    body: schemas.LoginRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    # Authenticate user
    user = await crud.user.authenticate(db, username=body.username, password=body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Update last login
    await crud.user.update_last_login(db, user_id=user.id)

    # Create tokens
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "warehouse_id": str(user.warehouse_id) if user.warehouse_id else None,
            "type": "access",
        },
        expires_delta=access_token_expires,
    )
    refresh_token = security.create_refresh_token(data={"sub": str(user.id), "type": "refresh"})

    # Build Pydantic object manually
    user_data = schemas.UserLoginResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        warehouse_id=user.warehouse_id,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_data
    }




# ============================================================
# REFRESH TOKEN
# ============================================================
@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(
    body: schemas.RefreshTokenRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Refresh access token dengan refresh token.
    Contoh payload:
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    """
    try:
        payload = security.decode_token(body.refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = await crud.user.get(db, id=user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # PERBAIKAN: gunakan JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "warehouse_id": str(user.warehouse_id) if user.warehouse_id else None,
                "type": "access",
            },
            expires_delta=access_token_expires,
        )
        refresh_token = security.create_refresh_token(data={"sub": str(user.id), "type": "refresh"})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # PERBAIKAN
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )


# ============================================================
# GET CURRENT USER
# ============================================================
@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user(
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get current authenticated user information.
    """
    return current_user


# ============================================================
# CHANGE PASSWORD
# ============================================================
@router.post("/change-password")
async def change_password(
    body: schemas.ChangePasswordRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Change password for current user.
    Contoh payload:
    {
        "current_password": "oldpassword",
        "new_password": "NewPassword123",
        "confirm_password": "NewPassword123"
    }
    """
    # Verify current password
    user = await crud.user.authenticate(
        db, 
        username=current_user.username, 
        password=body.current_password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    await crud.user.update(
        db, 
        db_obj=user, 
        obj_in={"password": body.new_password}
    )
    
    return {"message": "Password updated successfully"}