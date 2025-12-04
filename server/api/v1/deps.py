from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from server.core.database import get_db
from server.core.security import decode_token
from server import crud, schemas
from server.models.user import UserRole

security = HTTPBearer()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> schemas.UserInDB:
    """
    Get current authenticated user.
    Debug-friendly and robust version.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    print("Received token:", token)

    try:
        payload = decode_token(token)
        print("Decoded payload:", payload)
    except JWTError as e:
        print("JWT decode error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is empty",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    token_type: Optional[str] = payload.get("type")

    if not user_id or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload or wrong token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ambil user dari DB
    user = await crud.user.get(db, id=user_id)
    if not user:
        print("User not found for user_id:", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        print("User inactive:", user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return schemas.UserInDB.from_orm(user)


async def get_current_active_superadmin(
    current_user: schemas.UserInDB = Depends(get_current_user),
) -> schemas.UserInDB:
    """Return user if role is SUPER_ADMIN."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


async def get_current_active_gudang(
    current_user: schemas.UserInDB = Depends(get_current_user),
) -> schemas.UserInDB:
    """Return user if role is GUDANG (warehouse staff)."""
    if current_user.role != UserRole.GUDANG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    if not current_user.warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Warehouse staff must be assigned to a warehouse",
        )

    return current_user


def get_warehouse_filter(
    current_user: schemas.UserInDB = Depends(get_current_user),
) -> Optional[UUID]:
    """Return warehouse_id if user role is GUDANG, else None."""
    return current_user.warehouse_id if current_user.role == UserRole.GUDANG else None
