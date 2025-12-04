from typing import Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
import csv
import io
from sqlalchemy.ext.asyncio import AsyncSession
from server import crud, schemas
from server.api.v1 import deps
from server.models.user import UserRole
from server.utils.export import generate_inventory_report

router = APIRouter(tags=["reports"])

@router.get("/inventory/summary")
async def get_inventory_summary_report(
    *,
    db: AsyncSession = Depends(deps.get_db),
    warehouse_id: Optional[UUID] = Query(None),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get detailed inventory summary report.
    """
    # Set warehouse filter based on user role
    if current_user.role == UserRole.GUDANG:
        filter_warehouse_id = current_user.warehouse_id
    else:
        filter_warehouse_id = warehouse_id
    
    # Get summary
    summary = await crud.inventory_item.get_inventory_summary(
        db, warehouse_id=filter_warehouse_id
    )
    
    # Get low stock items
    if filter_warehouse_id:
        low_stock_items = await crud.inventory_item.get_low_stock_items(
            db, warehouse_id=filter_warehouse_id
        )
        out_of_stock_items = await crud.inventory_item.get_out_of_stock_items(
            db, warehouse_id=filter_warehouse_id
        )
    else:
        low_stock_items = await crud.inventory_item.get_low_stock_items(db)
        out_of_stock_items = await crud.inventory_item.get_out_of_stock_items(db)
    
    # Get recent transactions
    from datetime import datetime, timedelta
    from sqlalchemy import select, desc
    from server.models.transactions import Transaction
    
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    
    stmt = (
        select(Transaction)
        .where(Transaction.created_at >= one_week_ago)
        .order_by(desc(Transaction.created_at))
        .limit(10)
    )
    
    if filter_warehouse_id:
        from server.models.inventory import InventoryItem
        stmt = (
            stmt.join(InventoryItem, Transaction.item_id == InventoryItem.id)
            .where(InventoryItem.warehouse_id == filter_warehouse_id)
        )
    
    result = await db.execute(stmt)
    recent_transactions = result.scalars().all()
    
    return {
        "summary": summary,
        "low_stock_items": [
            {
                "id": item.id,
                "sku": item.sku,
                "name": item.name,
                "current_stock": item.current_stock,
                "min_stock": item.min_stock,
                "warehouse": item.warehouse.name if item.warehouse else None,
            }
            for item in low_stock_items[:20]  # Limit to 20 items
        ],
        "out_of_stock_items": [
            {
                "id": item.id,
                "sku": item.sku,
                "name": item.name,
                "warehouse": item.warehouse.name if item.warehouse else None,
            }
            for item in out_of_stock_items[:20]  # Limit to 20 items
        ],
        "recent_transactions": [
            {
                "id": tx.id,
                "transaction_code": tx.transaction_code,
                "item_name": tx.item.name if tx.item else None,
                "transaction_type": tx.transaction_type,
                "quantity": tx.quantity,
                "total_price": tx.total_price,
                "created_at": tx.created_at,
            }
            for tx in recent_transactions
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }

@router.get("/sales")
async def get_sales_report(
    *,
    db: AsyncSession = Depends(deps.get_db),
    start_date: datetime = Query(datetime.utcnow() - timedelta(days=30)),
    end_date: datetime = Query(datetime.utcnow()),
    warehouse_id: Optional[UUID] = Query(None),
    group_by: str = Query("day", regex="^(day|week|month)$"),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get sales report with various aggregations.
    """
    # Set warehouse filter based on user role
    if current_user.role == UserRole.GUDANG:
        filter_warehouse_id = current_user.warehouse_id
    else:
        filter_warehouse_id = warehouse_id
    
    # Get sales report
    report = await crud.transaction.get_sales_report(
        db,
        warehouse_id=filter_warehouse_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    # Additional analysis
    from sqlalchemy import select, func, case
    from server.models.transactions import Transaction
    from server.models.inventory import InventoryItem
    from server.models import Category
    
    # Get top selling items
    stmt = (
        select(
            InventoryItem.name,
            InventoryItem.sku,
            func.sum(Transaction.quantity).label("total_quantity"),
            func.sum(Transaction.total_price).label("total_sales"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .join(Transaction, InventoryItem.id == Transaction.item_id)
        .where(Transaction.transaction_type == "out")
        .where(Transaction.created_at >= start_date)
        .where(Transaction.created_at <= end_date)
    )
    
    if filter_warehouse_id:
        stmt = stmt.where(InventoryItem.warehouse_id == filter_warehouse_id)
    
    stmt = stmt.group_by(InventoryItem.id, InventoryItem.name, InventoryItem.sku)
    stmt = stmt.order_by(func.sum(Transaction.total_price).desc())
    stmt = stmt.limit(10)
    
    result = await db.execute(stmt)
    top_items = result.all()
    
    # Get sales by category
    from server.models import Category
    
    stmt = (
        select(
            Category.name,
            func.sum(Transaction.quantity).label("total_quantity"),
            func.sum(Transaction.total_price).label("total_sales"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .select_from(Transaction)
        .join(InventoryItem, Transaction.item_id == InventoryItem.id)
        .join(Category, InventoryItem.category_id == Category.id)
        .where(Transaction.transaction_type == "out")
        .where(Transaction.created_at >= start_date)
        .where(Transaction.created_at <= end_date)
    )
    
    if filter_warehouse_id:
        stmt = stmt.where(InventoryItem.warehouse_id == filter_warehouse_id)
    
    stmt = stmt.group_by(Category.id, Category.name)
    stmt = stmt.order_by(func.sum(Transaction.total_price).desc())
    
    result = await db.execute(stmt)
    sales_by_category = result.all()
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "days": (end_date - start_date).days,
        },
        "sales_summary": report["summary"],
        "daily_sales": report["daily_sales"],
        "top_selling_items": [
            {
                "name": row.name,
                "sku": row.sku,
                "total_quantity": row.total_quantity,
                "total_sales": row.total_sales,
                "transaction_count": row.transaction_count,
                "average_price": row.total_sales / row.total_quantity if row.total_quantity > 0 else 0,
            }
            for row in top_items
        ],
        "sales_by_category": [
            {
                "category": row.name,
                "total_quantity": row.total_quantity,
                "total_sales": row.total_sales,
                "transaction_count": row.transaction_count,
                "percentage": (row.total_sales / report["summary"]["total_sales"] * 100) 
                if report["summary"]["total_sales"] > 0 else 0,
            }
            for row in sales_by_category
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }

@router.get("/inventory/export")
async def export_inventory_report(
    *,
    db: AsyncSession = Depends(deps.get_db),
    warehouse_id: Optional[UUID] = Query(None),
    format: str = Query("csv", regex="^(csv|json)$"),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Export inventory report.
    """
    # Set warehouse filter based on user role
    if current_user.role == UserRole.GUDANG:
        filter_warehouse_id = current_user.warehouse_id
    else:
        filter_warehouse_id = warehouse_id
    
    # Generate report
    report = await generate_inventory_report(
        db, warehouse_id=filter_warehouse_id, format=format
    )
    
    if format == "csv":
        # Return CSV file
        return StreamingResponse(
            io.StringIO(report["data"]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={report['filename']}"
            }
        )
    else:
        # Return JSON response
        return report

@router.get("/stock-movement/{item_id}")
async def get_stock_movement_report(
    *,
    db: AsyncSession = Depends(deps.get_db),
    item_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get stock movement report for a specific item.
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
            detail="Cannot access items from other warehouses",
        )
    
    # Get stock movement
    movement = await crud.transaction.get_stock_movement(
        db, item_id=item_id, days=days
    )
    
    # Calculate statistics
    transactions = await crud.transaction.get_by_item(db, item_id=item_id, limit=1000)
    
    total_in = sum(tx.quantity for tx in transactions if tx.transaction_type in ["in", "return"])
    total_out = sum(tx.quantity for tx in transactions if tx.transaction_type == "out")
    
    # Calculate average daily sales (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_sales = [
        tx for tx in transactions 
        if tx.transaction_type == "out" and tx.created_at >= thirty_days_ago
    ]
    
    avg_daily_sales = sum(tx.quantity for tx in recent_sales) / 30 if recent_sales else 0
    
    return {
        "item": {
            "id": item.id,
            "sku": item.sku,
            "name": item.name,
            "current_stock": item.current_stock,
            "min_stock": item.min_stock,
            "max_stock": item.max_stock,
        },
        "movement": movement,
        "statistics": {
            "total_stock_in": total_in,
            "total_stock_out": total_out,
            "net_movement": total_in - total_out,
            "turnover_rate": total_out / item.current_stock if item.current_stock > 0 else 0,
            "average_daily_sales": avg_daily_sales,
            "days_of_supply": item.current_stock / avg_daily_sales if avg_daily_sales > 0 else 0,
        },
    }

@router.get("/alerts")
async def get_alerts_report(
    *,
    db: AsyncSession = Depends(deps.get_db),
    alert_type: Optional[str] = Query(None, regex="^(low_stock|out_of_stock|over_stock)$"),
    is_read: Optional[bool] = Query(None),
    days: int = Query(7, ge=1, le=30),
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Get stock alerts report.
    """
    # Set warehouse filter based on user role
    warehouse_id = None
    if current_user.role == UserRole.GUDANG:
        warehouse_id = current_user.warehouse_id
    
    # Get alerts
    from datetime import datetime, timedelta
    from sqlalchemy import select, and_
    from server.models.transactions import StockAlert
    from server.models.inventory import InventoryItem
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    stmt = (
        select(StockAlert)
        .join(InventoryItem, StockAlert.item_id == InventoryItem.id)
        .where(StockAlert.created_at >= cutoff_date)
    )
    
    if warehouse_id:
        stmt = stmt.where(InventoryItem.warehouse_id == warehouse_id)
    
    if alert_type:
        stmt = stmt.where(StockAlert.alert_type == alert_type)
    
    if is_read is not None:
        stmt = stmt.where(StockAlert.is_read == is_read)
    
    stmt = stmt.order_by(StockAlert.created_at.desc())
    
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    
    # Count by type
    alert_counts = {}
    for alert in alerts:
        alert_counts[alert.alert_type] = alert_counts.get(alert.alert_type, 0) + 1
    
    return {
        "alerts": [
            {
                "id": alert.id,
                "item_id": alert.item_id,
                "item_name": alert.item.name if alert.item else None,
                "alert_type": alert.alert_type,
                "current_stock": alert.current_stock,
                "threshold": alert.threshold,
                "message": alert.message,
                "is_read": alert.is_read,
                "created_at": alert.created_at,
                "read_at": alert.read_at,
            }
            for alert in alerts
        ],
        "summary": {
            "total_alerts": len(alerts),
            "unread_alerts": len([a for a in alerts if not a.is_read]),
            "alert_counts": alert_counts,
            "period_days": days,
        },
        "generated_at": datetime.utcnow().isoformat(),
    }