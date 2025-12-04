from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from server import crud
from server.models.inventory import InventoryItem
from server.models.transactions import StockAlert

async def check_stock_alerts(
    db: AsyncSession,
    *,
    item_id: UUID,
    item: Optional[InventoryItem] = None,
) -> None:
    """
    Check and create stock alerts for an item.
    """
    if not item:
        item = await crud.inventory_item.get(db, id=item_id)
    
    if not item:
        return
    
    # Check for low stock alert
    if item.current_stock <= item.min_stock and item.current_stock > 0:
        # Check if alert already exists
        stmt = select(StockAlert).where(
            StockAlert.item_id == item_id,
            StockAlert.alert_type == "low_stock",
            StockAlert.is_read == False,
            StockAlert.created_at >= datetime.utcnow() - timedelta(hours=24),
        )
        result = await db.execute(stmt)
        existing_alert = result.scalar_one_or_none()
        
        if not existing_alert:
            await crud.stock_alert.create_alert(
                db,
                item_id=item_id,
                alert_type="low_stock",
                current_stock=item.current_stock,
                threshold=item.min_stock,
            )
    
    # Check for out of stock alert
    elif item.current_stock == 0:
        stmt = select(StockAlert).where(
            StockAlert.item_id == item_id,
            StockAlert.alert_type == "out_of_stock",
            StockAlert.is_read == False,
            StockAlert.created_at >= datetime.utcnow() - timedelta(hours=24),
        )
        result = await db.execute(stmt)
        existing_alert = result.scalar_one_or_none()
        
        if not existing_alert:
            await crud.stock_alert.create_alert(
                db,
                item_id=item_id,
                alert_type="out_of_stock",
                current_stock=0,
                threshold=0,
            )
    
    # Check for over stock alert
    elif item.max_stock and item.current_stock >= item.max_stock:
        stmt = select(StockAlert).where(
            StockAlert.item_id == item_id,
            StockAlert.alert_type == "over_stock",
            StockAlert.is_read == False,
            StockAlert.created_at >= datetime.utcnow() - timedelta(hours=24),
        )
        result = await db.execute(stmt)
        existing_alert = result.scalar_one_or_none()
        
        if not existing_alert:
            await crud.stock_alert.create_alert(
                db,
                item_id=item_id,
                alert_type="over_stock",
                current_stock=item.current_stock,
                threshold=item.max_stock,
            )

async def check_all_stock_alerts(db: AsyncSession, warehouse_id: Optional[UUID] = None) -> None:
    """
    Check stock alerts for all items in a warehouse.
    """
    if warehouse_id:
        items = await crud.inventory_item.get_multi_by_warehouse(
            db, warehouse_id=warehouse_id, limit=1000  # Add limit for safety
        )
    else:
        items = await crud.inventory_item.get_multi(db, limit=1000)
    
    for item in items:
        await check_stock_alerts(db, item_id=item.id, item=item)

async def mark_alerts_as_read(
    db: AsyncSession,
    alert_ids: List[UUID],
    user_id: UUID
) -> List[StockAlert]:
    """
    Mark multiple alerts as read.
    """
    updated_alerts = []
    for alert_id in alert_ids:
        try:
            alert = await crud.stock_alert.mark_as_read(
                db, alert_id=alert_id, user_id=user_id
            )
            updated_alerts.append(alert)
        except ValueError:
            # Alert not found, skip
            continue
    
    return updated_alerts

async def get_unread_alerts_count(
    db: AsyncSession,
    warehouse_id: Optional[UUID] = None
) -> int:
    """
    Get count of unread alerts.
    """
    from sqlalchemy import func
    from server.models.transactions import StockAlert
    from server.models.inventory import InventoryItem
    
    stmt = select(func.count(StockAlert.id)).where(StockAlert.is_read == False)
    
    if warehouse_id:
        stmt = stmt.join(
            InventoryItem, StockAlert.item_id == InventoryItem.id
        ).where(InventoryItem.warehouse_id == warehouse_id)
    
    result = await db.execute(stmt)
    return result.scalar() or 0