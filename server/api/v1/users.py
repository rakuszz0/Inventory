from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from server import crud, schemas
from server.api.v1 import deps
from server.models.user import UserRole

router = APIRouter(tags=["users"])

# ============================================================
# GET USERS
# ============================================================
@router.get("/", response_model=List[schemas.UserResponse])
async def read_users(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[UserRole] = None,
    warehouse_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superadmin),
) -> Any:
    users = await crud.user.get_multi(db, skip=skip, limit=limit)
    filtered_users = [
        u for u in users
        if (not role or u.role == role)
        and (not warehouse_id or u.warehouse_id == warehouse_id)
        and (is_active is None or u.is_active == is_active)
    ]
    return filtered_users


# ============================================================
# CREATE USER
# ============================================================
@router.post("/", response_model=schemas.UserResponse)
async def create_user(
    db: AsyncSession = Depends(deps.get_db),
    user_in: schemas.UserCreate = ...,
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superadmin),
) -> Any:
    if user_in.role == UserRole.GUDANG and not user_in.warehouse_id:
        raise HTTPException(status_code=400, detail="Warehouse staff must be assigned to a warehouse")
    if user_in.warehouse_id:
        warehouse = await crud.warehouse.get(db, id=user_in.warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=400, detail="Warehouse not found")
    user = await crud.user.create(db, obj_in=user_in)
    return user


# ============================================================
# GET USER BY ID
# ============================================================
@router.get("/{user_id}", response_model=schemas.UserResponse)
async def read_user(
    db: AsyncSession = Depends(deps.get_db),
    user_id: UUID = ...,
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superadmin),
) -> Any:
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ============================================================
# UPDATE USER
# ============================================================
@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    db: AsyncSession = Depends(deps.get_db),
    user_id: UUID = ...,
    user_in: schemas.UserUpdate = ...,
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superadmin),
) -> Any:
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_in.role == UserRole.SUPER_ADMIN and user_in.warehouse_id:
        raise HTTPException(status_code=400, detail="Super admin cannot be assigned to a warehouse")
    if user_in.warehouse_id:
        warehouse = await crud.warehouse.get(db, id=user_in.warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=400, detail="Warehouse not found")
    user = await crud.user.update(db, db_obj=user, obj_in=user_in)
    return user


# ============================================================
# DELETE USER (soft delete)
# ============================================================
@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    db: AsyncSession = Depends(deps.get_db),
    user_id: UUID = ...,
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superadmin),
) -> Any:
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await crud.user.update(db, db_obj=user, obj_in={"is_active": False})
    return {"message": "User deactivated successfully"}


# ============================================================
# GET USERS BY WAREHOUSE
# ============================================================
@router.get("/warehouse/{warehouse_id}", response_model=List[schemas.UserResponse])
async def read_users_by_warehouse(
    db: AsyncSession = Depends(deps.get_db),
    warehouse_id: UUID = ...,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superadmin),
) -> Any:
    users = await crud.user.get_by_warehouse(db, warehouse_id=warehouse_id, skip=skip, limit=limit)
    return users


# ============================================================
# ACTIVATE USER
# ============================================================
@router.post("/{user_id}/activate")
async def activate_user(
    db: AsyncSession = Depends(deps.get_db),
    user_id: UUID = ...,
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superadmin),
) -> Any:
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await crud.user.update(db, db_obj=user, obj_in={"is_active": True})
    return {"message": "User activated successfully"}
