from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from server import schemas 
from server import crud
from server.api.v1 import deps
from server.models.user import UserRole

router = APIRouter(tags=["inventory"])

# ==================== ENDPOINT UTAMA UNTUK FRONTEND ====================

@router.get("/", response_model=schemas.PaginatedInventoryResponse)
async def read_inventory_items_paginated(
    *,
    db: AsyncSession = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    warehouse_id: Optional[UUID] = Query(None),
    category_id: Optional[UUID] = Query(None),
    min_stock: Optional[int] = Query(None, ge=0),
    max_stock: Optional[int] = Query(None, ge=0),
    search: Optional[str] = Query(None),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve inventory items with pagination - ENDPOINT UTAMA FRONTEND
    """
    # Set warehouse filter based on user role
    user_warehouse_id = None
    if current_user.role == UserRole.GUDANG:
        user_warehouse_id = current_user.warehouse_id
    
    # Apply warehouse filter
    filter_warehouse_id = warehouse_id or user_warehouse_id
    
    # Calculate skip
    skip = (page - 1) * limit
    
    # Get items with total count
    items, total = await crud.inventory_item.get_multi_filtered_with_count(
        db,
        warehouse_id=filter_warehouse_id,
        category_id=category_id,
        min_stock=min_stock,
        max_stock=max_stock,
        skip=skip,
        limit=limit,
        search=search
    )
    
    # Calculate total pages
    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": total_pages
        }
    }

@router.get("/value", response_model=schemas.InventoryValueResponse)
async def get_inventory_value(
    *,
    db: AsyncSession = Depends(deps.get_db),
    warehouse_id: Optional[UUID] = Query(None),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get total inventory value.
    """
    # Set warehouse filter based on user role
    if current_user.role == UserRole.GUDANG:
        filter_warehouse_id = current_user.warehouse_id
    else:
        filter_warehouse_id = warehouse_id
    
    # Calculate inventory value
    total_value = await crud.inventory_item.get_total_inventory_value(
        db, warehouse_id=filter_warehouse_id
    )
    
    return {
        "value": total_value,
        "currency": "IDR",
        "warehouse_id": filter_warehouse_id
    }

@router.get("/low-stock", response_model=List[schemas.InventoryItemResponse])
async def get_low_stock_items(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get items with low stock.
    """
    if current_user.role == UserRole.GUDANG:
        items = await crud.inventory_item.get_low_stock_items(
            db, warehouse_id=current_user.warehouse_id
        )
    else:
        items = await crud.inventory_item.get_low_stock_items(db)
    
    return items

# ==================== ENDPOINT CRUD ITEMS ====================

@router.post("/", response_model=schemas.InventoryItemResponse)
async def create_inventory_item(
    *,
    db: AsyncSession = Depends(deps.get_db),
    item_in: schemas.InventoryItemCreate,
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Create new inventory item.
    """
    # Check if user has permission (only gudang role can create items)
    if current_user.role != UserRole.GUDANG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only warehouse staff can create items",
        )
    
    # Check if warehouse exists
    warehouse = await crud.warehouse.get(db, id=current_user.warehouse_id)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Warehouse not found",
        )
    
    # Check if category exists
    category = await crud.category.get(db, id=item_in.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found",
        )
    
    # Generate SKU
    import uuid as uuid_lib
    sku = f"ITEM-{uuid_lib.uuid4().hex[:8].upper()}"
    
    # Create item
    item_data = item_in.dict()
    item_data.update({
        "sku": sku,
        "warehouse_id": current_user.warehouse_id,
        "created_by": current_user.id,
    })
    
    item = await crud.inventory_item.create(db, obj_in=schemas.InventoryItemCreate(**item_data))
    
    # Record initial stock transaction
    if item_in.current_stock > 0:
        transaction_data = schemas.TransactionCreate(
            item_id=item.id,
            transaction_type="in",
            quantity=item_in.current_stock,
            unit_price=item_in.buy_price,
            reference="Initial stock",
            notes="Initial stock creation",
        )
        
        await crud.transaction.create_with_stock_check(
            db,
            obj_in=transaction_data,
            user_id=current_user.id,
            item_id=item.id,
            previous_stock=0,
            new_stock=item_in.current_stock,
        )
    
    return item

@router.get("/{item_id}", response_model=schemas.InventoryItemResponse)
async def read_inventory_item(
    *,
    db: AsyncSession = Depends(deps.get_db),
    item_id: UUID,
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get inventory item by ID.
    """
    item = await crud.inventory_item.get_with_details(db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    
    # Check warehouse access for gudang role
    if (current_user.role == UserRole.GUDANG and 
        item.warehouse_id != current_user.warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return item

@router.put("/{item_id}", response_model=schemas.InventoryItemResponse)
async def update_inventory_item(
    *,
    db: AsyncSession = Depends(deps.get_db),
    item_id: UUID,
    item_in: schemas.InventoryItemUpdate,
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Update inventory item.
    """
    item = await crud.inventory_item.get_with_details(db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    
    # Check permissions
    if current_user.role == UserRole.GUDANG:
        if item.warehouse_id != current_user.warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update items from other warehouses",
            )
        
        # Warehouse staff cannot change certain fields
        restricted_fields = ["warehouse_id", "created_by", "is_active"]
        for field in restricted_fields:
            if getattr(item_in, field, None) is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Cannot update {field} field",
                )
    
    # Validate stock update
    if item_in.current_stock is not None:
        if item_in.current_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock cannot be negative",
            )
        
        # Record adjustment transaction if stock changed
        if item_in.current_stock != item.current_stock:
            adjustment = item_in.current_stock - item.current_stock
            transaction_type = "in" if adjustment > 0 else "out"
            
            transaction_data = schemas.TransactionCreate(
                item_id=item.id,
                transaction_type=transaction_type,
                quantity=abs(adjustment),
                unit_price=item.buy_price if adjustment > 0 else item.sell_price,
                reference="Manual adjustment",
                notes=f"Stock adjusted from {item.current_stock} to {item_in.current_stock}",
            )
            
            await crud.transaction.create_with_stock_check(
                db,
                obj_in=transaction_data,
                user_id=current_user.id,
                item_id=item.id,
                previous_stock=item.current_stock,
                new_stock=item_in.current_stock,
            )
    
    # Update item
    item = await crud.inventory_item.update(db, db_obj=item, obj_in=item_in)
    return item

@router.delete("/{item_id}")
async def delete_inventory_item(
    *,
    db: AsyncSession = Depends(deps.get_db),
    item_id: UUID,
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Delete inventory item.
    """
    item = await crud.inventory_item.get(db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    
    # Check permissions
    if current_user.role == UserRole.GUDANG:
        if item.warehouse_id != current_user.warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete items from other warehouses",
            )
    
    # Check if item can be deleted (stock must be 0)
    if item.current_stock > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete item with stock > 0",
        )
    
    # Delete item
    await crud.inventory_item.delete(db, id=item_id)
    return {"message": "Item deleted successfully"}

@router.post("/{item_id}/adjust-stock")
async def adjust_item_stock(
    *,
    db: AsyncSession = Depends(deps.get_db),
    item_id: UUID,
    adjustment: schemas.StockAdjustmentRequest,
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Adjust item stock (increase or decrease).
    """
    item = await crud.inventory_item.get(db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    
    # Check permissions
    if current_user.role == UserRole.GUDANG:
        if item.warehouse_id != current_user.warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot adjust stock for items from other warehouses",
            )
    
    # Calculate new stock
    if adjustment.transaction_type in ["out", "adjustment"] and adjustment.quantity > 0:
        # For out transactions, quantity should be negative
        quantity = -adjustment.quantity
    else:
        quantity = adjustment.quantity
    
    new_stock = item.current_stock + quantity
    
    # Validate new stock
    if new_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock",
        )
    
    # Get appropriate price
    unit_price = item.buy_price if quantity > 0 else item.sell_price
    
    # Create transaction
    transaction_data = schemas.TransactionCreate(
        item_id=item.id,
        transaction_type=adjustment.transaction_type,
        quantity=abs(quantity),
        unit_price=unit_price,
        reference=adjustment.reference,
        notes=adjustment.notes,
    )
    
    await crud.transaction.create_with_stock_check(
        db,
        obj_in=transaction_data,
        user_id=current_user.id,
        item_id=item.id,
        previous_stock=item.current_stock,
        new_stock=new_stock,
    )
    
    # Update item stock
    previous_stock = item.current_stock
    item = await crud.inventory_item.update_stock(db, item_id=item_id, new_stock=new_stock)
    
    # Check for stock alerts
    from server.utils.alert import check_stock_alerts
    await check_stock_alerts(db, item_id=item_id)
    
    return {
        "message": "Stock adjusted successfully",
        "item": schemas.InventoryItemResponse.from_orm(item),
        "previous_stock": previous_stock,
        "new_stock": new_stock,
        "adjustment": quantity,
    }

@router.get("/{item_id}/transactions", response_model=List[schemas.TransactionResponse])
async def get_item_transactions(
    *,
    db: AsyncSession = Depends(deps.get_db),
    item_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get transactions for a specific item.
    """
    item = await crud.inventory_item.get(db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    
    # Check warehouse access for gudang role
    if (current_user.role == UserRole.GUDANG and 
        item.warehouse_id != current_user.warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    transactions = await crud.transaction.get_by_item(
        db, item_id=item_id, skip=skip, limit=limit
    )
    
    return [schemas.TransactionResponse.from_orm(tx) for tx in transactions]

# ==================== ENDPOINT SUMMARY & LAPORAN ====================

@router.get("/summary", response_model=schemas.InventorySummary)
async def get_inventory_summary(
    *,
    db: AsyncSession = Depends(deps.get_db),
    warehouse_id: Optional[UUID] = Query(None),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get inventory summary statistics.
    """
    # Set warehouse filter based on user role
    if current_user.role == UserRole.GUDANG:
        filter_warehouse_id = current_user.warehouse_id
    else:
        filter_warehouse_id = warehouse_id
    
    summary = await crud.inventory_item.get_inventory_summary(
        db, warehouse_id=filter_warehouse_id
    )
    return summary

@router.get("/out-of-stock", response_model=List[schemas.InventoryItemResponse])
async def get_out_of_stock_items(
    *,
    db: AsyncSession = Depends(deps.get_db),
    warehouse_id: Optional[UUID] = Query(None),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get items that are out of stock.
    """
    # Set warehouse filter based on user role
    filter_warehouse_id = None
    if current_user.role == UserRole.GUDANG:
        filter_warehouse_id = current_user.warehouse_id
    else:
        filter_warehouse_id = warehouse_id
    
    items = await crud.inventory_item.get_out_of_stock_items(
        db, warehouse_id=filter_warehouse_id
    )
    
    return [schemas.InventoryItemResponse.from_orm(item) for item in items]

# ==================== ENDPOINT DEPRECATED (untuk backward compatibility) ====================

@router.get("/items", response_model=List[schemas.InventoryItemResponse], deprecated=True)
async def read_inventory_items_legacy(
    *,
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    warehouse_id: Optional[UUID] = Query(None),
    category_id: Optional[UUID] = Query(None),
    min_stock: Optional[int] = Query(None, ge=0),
    max_stock: Optional[int] = Query(None, ge=0),
    search: Optional[str] = Query(None),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    DEPRECATED: Use GET /inventory/ instead.
    Retrieve inventory items.
    """
    # Set warehouse filter based on user role
    user_warehouse_id = None
    if current_user.role == UserRole.GUDANG:
        user_warehouse_id = current_user.warehouse_id
    
    # Apply warehouse filter
    filter_warehouse_id = warehouse_id or user_warehouse_id
    
    # Get items
    items = await crud.inventory_item.get_multi_filtered(
        db,
        warehouse_id=filter_warehouse_id,
        category_id=category_id,
        min_stock=min_stock,
        max_stock=max_stock,
        skip=skip,
        limit=limit,
    )
    
    # Apply search filter if provided
    if search:
        items = [
            item for item in items
            if search.lower() in item.name.lower()
            or search.lower() in item.sku.lower()
            or (item.barcode and search.lower() in item.barcode.lower())
        ]
    
    return items