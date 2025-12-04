# server/api/v1/transactions.py
from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from server import crud, schemas
from server.api.v1 import deps
from server.models.user import UserRole
from server.models.transactions import TransactionType

router = APIRouter(tags=["transactions"])

@router.get("/", response_model=List[schemas.TransactionResponse])
async def read_transactions(
    *,
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    item_id: Optional[UUID] = Query(None),
    warehouse_id: Optional[UUID] = Query(None),
    transaction_type: Optional[TransactionType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve transactions.
    """
    # Set warehouse filter based on user role
    user_warehouse_id = None
    if current_user.role == UserRole.GUDANG:
        user_warehouse_id = current_user.warehouse_id
    
    # Apply warehouse filter
    filter_warehouse_id = warehouse_id or user_warehouse_id
    
    if item_id:
        # Get transactions for specific item
        transactions = await crud.transaction.get_by_item(
            db, item_id=item_id, skip=skip, limit=limit
        )
    elif filter_warehouse_id:
        # Get transactions for specific warehouse
        transactions = await crud.transaction.get_by_warehouse(
            db,
            warehouse_id=filter_warehouse_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
    else:
        # Get all transactions (super admin only)
        if current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin only can view all transactions",
            )
        
        # Base query for all transactions
        from sqlalchemy import select
        from server.models.transactions import Transaction
        from server.models.inventory import InventoryItem
        
        stmt = select(Transaction)
        
        # Join with inventory items for warehouse filter
        if filter_warehouse_id:
            stmt = stmt.join(InventoryItem, Transaction.item_id == InventoryItem.id)
            stmt = stmt.where(InventoryItem.warehouse_id == filter_warehouse_id)
        
        # Apply transaction type filter
        if transaction_type:
            stmt = stmt.where(Transaction.transaction_type == transaction_type)
        
        # Apply date filters
        if start_date:
            stmt = stmt.where(Transaction.created_at >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.created_at <= end_date)
        
        stmt = stmt.order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        transactions = result.scalars().all()
    
    # Filter by transaction type if specified
    if transaction_type and transactions:
        transactions = [tx for tx in transactions if tx.transaction_type == transaction_type]
    
    return transactions

@router.get("/{transaction_id}", response_model=schemas.TransactionResponse)
async def read_transaction(
    *,
    db: AsyncSession = Depends(deps.get_db),
    transaction_id: UUID,
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get transaction by ID.
    """
    transaction = await crud.transaction.get(db, id=transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    
    # Check warehouse access for gudang role
    if current_user.role == UserRole.GUDANG:
        # Get item to check warehouse
        item = await crud.inventory_item.get(db, id=transaction.item_id)
        if item.warehouse_id != current_user.warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access transactions from other warehouses",
            )
    
    return transaction

@router.post("/stock-in")
async def create_stock_in_transaction(
    *,
    db: AsyncSession = Depends(deps.get_db),
    transaction_in: schemas.TransactionCreate,
    current_user: schemas.UserInDB = Depends(deps.get_current_active_gudang),
) -> Any:
    """
    Create stock in transaction. (Gudang only)
    """
    # Validate transaction type
    if transaction_in.transaction_type not in ["in", "return"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction type must be 'in' or 'return' for stock in",
        )
    
    # Get item
    item = await crud.inventory_item.get(db, id=transaction_in.item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    
    # Check warehouse access
    if item.warehouse_id != current_user.warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot add stock to items from other warehouses",
        )
    
    # Calculate new stock
    new_stock = item.current_stock + transaction_in.quantity
    
    # Create transaction
    transaction = await crud.transaction.create_with_stock_check(
        db,
        obj_in=transaction_in,
        user_id=current_user.id,
        item_id=transaction_in.item_id,
        previous_stock=item.current_stock,
        new_stock=new_stock,
    )
    
    # Update item stock
    await crud.inventory_item.update_stock(
        db, item_id=transaction_in.item_id, new_stock=new_stock
    )
    
    # Update item prices if this is a purchase
    if transaction_in.transaction_type == "in" and transaction_in.unit_price:
        await crud.inventory_item.update(
            db,
            db_obj=item,
            obj_in={
                "last_buy_price": transaction_in.unit_price,
                "buy_price": transaction_in.unit_price,
            }
        )
    
    # Check for stock alerts
    from server.utils.alert import check_stock_alerts
    await check_stock_alerts(db, item_id=transaction_in.item_id)
    
    return {
        "message": "Stock in transaction created successfully",
        "transaction": schemas.TransactionResponse.from_orm(transaction),
        "new_stock": new_stock,
    }

@router.post("/stock-out")
async def create_stock_out_transaction(
    *,
    db: AsyncSession = Depends(deps.get_db),
    transaction_in: schemas.TransactionCreate,
    current_user: schemas.UserInDB = Depends(deps.get_current_active_gudang),
) -> Any:
    """
    Create stock out transaction (sale). (Gudang only)
    """
    # Validate transaction type
    if transaction_in.transaction_type != "out":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction type must be 'out' for stock out",
        )
    
    # Get item
    item = await crud.inventory_item.get(db, id=transaction_in.item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    
    # Check warehouse access
    if item.warehouse_id != current_user.warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot sell items from other warehouses",
        )
    
    # Check if enough stock
    if item.current_stock < transaction_in.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available: {item.current_stock}, Requested: {transaction_in.quantity}",
        )
    
    # Calculate new stock
    new_stock = item.current_stock - transaction_in.quantity
    
    # Use sell price if unit_price not provided
    if not transaction_in.unit_price:
        transaction_in.unit_price = item.sell_price
    
    # Create transaction
    transaction = await crud.transaction.create_with_stock_check(
        db,
        obj_in=transaction_in,
        user_id=current_user.id,
        item_id=transaction_in.item_id,
        previous_stock=item.current_stock,
        new_stock=new_stock,
    )
    
    # Update item stock
    await crud.inventory_item.update_stock(
        db, item_id=transaction_in.item_id, new_stock=new_stock
    )
    
    # Update last sold price
    if transaction_in.unit_price:
        await crud.inventory_item.update(
            db,
            db_obj=item,
            obj_in={"last_sell_price": transaction_in.unit_price}
        )
    
    # Check for stock alerts
    from server.utils.alert import check_stock_alerts
    await check_stock_alerts(db, item_id=transaction_in.item_id)
    
    return {
        "message": "Stock out transaction created successfully",
        "transaction": schemas.TransactionResponse.from_orm(transaction),
        "new_stock": new_stock,
        "total_sale": transaction.total_price,
    }

@router.get("/sales/today")
async def get_today_sales(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get today's sales.
    """
    today = datetime.utcnow().date()
    start_date = datetime.combine(today, datetime.min.time())
    end_date = datetime.combine(today, datetime.max.time())
    
    warehouse_id = None
    if current_user.role == UserRole.GUDANG:
        warehouse_id = current_user.warehouse_id
    
    report = await crud.transaction.get_sales_report(
        db,
        warehouse_id=warehouse_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    return report

@router.get("/sales/daily")
async def get_daily_sales(
    *,
    db: AsyncSession = Depends(deps.get_db),
    days: int = Query(7, ge=1, le=30),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get daily sales for the last N days.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    warehouse_id = None
    if current_user.role == UserRole.GUDANG:
        warehouse_id = current_user.warehouse_id
    
    report = await crud.transaction.get_sales_report(
        db,
        warehouse_id=warehouse_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    return report