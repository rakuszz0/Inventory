from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from server import crud, schemas
from server.api.v1 import deps
from server.models.user import UserRole
from typing import Optional

router = APIRouter(tags=["warehouses"])

@router.post("/", response_model=schemas.WarehouseResponse)
async def create_warehouse(
    *,
    db: AsyncSession = Depends(deps.get_db),
    warehouse_in: schemas.WarehouseCreate,
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superadmin),
) -> Any:
    """
    Create new warehouse. (Super Admin only)
    """
    # Check if warehouse code already exists
    existing_warehouse = await crud.warehouse.get_by_code(db, code=warehouse_in.code)
    if existing_warehouse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Warehouse with this code already exists",
        )
    
    # Create warehouse
    warehouse_data = warehouse_in.dict()
    warehouse_data["created_by"] = current_user.id
    
    warehouse = await crud.warehouse.create(db, obj_in=schemas.WarehouseCreate(**warehouse_data))
    return warehouse

@router.get("/", response_model=List[schemas.WarehouseResponse])
async def read_warehouses(
    *,
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve warehouses.
    """
    warehouses = await crud.warehouse.get_multi(db, skip=skip, limit=limit)
    
    # Apply active filter
    if is_active is not None:
        warehouses = [wh for wh in warehouses if wh.is_active == is_active]
    
    return warehouses

@router.get("/active", response_model=List[schemas.WarehouseResponse])
async def read_active_warehouses(
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Retrieve active warehouses.
    """
    warehouses = await crud.warehouse.get_active_warehouses(db)
    return warehouses

@router.get("/{warehouse_id}", response_model=schemas.WarehouseResponse)
async def read_warehouse(
    *,
    db: AsyncSession = Depends(deps.get_db),
    warehouse_id: UUID,
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get warehouse by ID.
    """
    warehouse = await crud.warehouse.get_with_items(db, id=warehouse_id)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )
    return warehouse

@router.put("/{warehouse_id}", response_model=schemas.WarehouseResponse)
async def update_warehouse(
    *,
    db: AsyncSession = Depends(deps.get_db),
    warehouse_id: UUID,
    warehouse_in: schemas.WarehouseUpdate,
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superadmin),
) -> Any:
    """
    Update warehouse. (Super Admin only)
    """
    warehouse = await crud.warehouse.get(db, id=warehouse_id)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )
    
    # Check if code already exists (if changing code)
    if warehouse_in.code and warehouse_in.code != warehouse.code:
        existing_warehouse = await crud.warehouse.get_by_code(db, code=warehouse_in.code)
        if existing_warehouse:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse with this code already exists",
            )
    
    warehouse = await crud.warehouse.update(db, db_obj=warehouse, obj_in=warehouse_in)
    return warehouse

@router.delete("/{warehouse_id}")
async def delete_warehouse(
    *,
    db: AsyncSession = Depends(deps.get_db),
    warehouse_id: UUID,
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superadmin),
) -> Any:
    """
    Delete warehouse. (Super Admin only)
    """
    warehouse = await crud.warehouse.get_with_items(db, id=warehouse_id)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )
    
    # Check if warehouse has items
    if warehouse.inventory_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete warehouse that has items",
        )
    
    # Check if warehouse has users
    from server.models.user import User
    from sqlalchemy import select
    
    stmt = select(User).where(User.warehouse_id == warehouse_id)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    if users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete warehouse that has users",
        )
    
    # Soft delete (set inactive)
    await crud.warehouse.update(db, db_obj=warehouse, obj_in={"is_active": False})
    
    return {"message": "Warehouse deactivated successfully"}

@router.get("/{warehouse_id}/summary")
async def get_warehouse_summary(
    *,
    db: AsyncSession = Depends(deps.get_db),
    warehouse_id: UUID,
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get warehouse inventory summary.
    """
    # Check access
    if current_user.role == UserRole.GUDANG and current_user.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other warehouses",
        )
    
    summary = await crud.inventory_item.get_inventory_summary(db, warehouse_id=warehouse_id)
    
    # Get recent alerts
    from datetime import datetime, timedelta
    from server.crud.transactions import stock_alert
    
    recent_alerts = await stock_alert.get_recent_alerts(
        db, days=7, warehouse_id=warehouse_id
    )
    
    return {
        "summary": summary,
        "recent_alerts": [
            {
                "id": alert.id,
                "item_id": alert.item_id,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "created_at": alert.created_at,
                "is_read": alert.is_read,
            }
            for alert in recent_alerts[:10]  # Limit to 10 recent alerts
        ]
    }