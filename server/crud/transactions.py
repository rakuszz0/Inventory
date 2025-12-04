import uuid 
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, case
from server.models.transactions import Transaction, StockAlert, TransactionType
from server.schemas.transactions import TransactionCreate 
from server.crud.base import CRUDBase

class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionCreate]):
    async def create_with_stock_check(
        self,
        db: AsyncSession,
        *,
        obj_in: TransactionCreate,
        user_id: UUID,
        item_id: UUID,
        previous_stock: int,
        new_stock: int,
    ) -> Transaction:
        """Create transaction with stock validation"""
        from server.models.inventory import InventoryItem
        
        # Generate transaction code
        transaction_code = f"TRX-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate total price if unit_price is provided
        total_price = None
        if obj_in.unit_price:
            total_price = obj_in.unit_price * abs(obj_in.quantity)
        
        db_obj = Transaction(
            transaction_code=transaction_code,
            item_id=item_id,
            transaction_type=obj_in.transaction_type,
            quantity=obj_in.quantity,
            unit_price=obj_in.unit_price,
            total_price=total_price,
            previous_stock=previous_stock,
            new_stock=new_stock,
            reference=obj_in.reference,
            notes=obj_in.notes,
            created_by=user_id,
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_by_item(
        self,
        db: AsyncSession,
        *,
        item_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Transaction]:
        """Get transactions for a specific item"""
        stmt = (
            select(Transaction)
            .where(Transaction.item_id == item_id)
            .order_by(desc(Transaction.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_by_warehouse(
        self,
        db: AsyncSession,
        *,
        warehouse_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Transaction]:
        """Get transactions for a warehouse"""
        from server.models.inventory import InventoryItem
        
        stmt = (
            select(Transaction)
            .join(InventoryItem, Transaction.item_id == InventoryItem.id)
            .where(InventoryItem.warehouse_id == warehouse_id)
        )
        
        # Apply date filters
        if start_date:
            stmt = stmt.where(Transaction.created_at >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.created_at <= end_date)
        
        stmt = stmt.order_by(desc(Transaction.created_at)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_sales_report(
        self,
        db: AsyncSession,
        *,
        warehouse_id: Optional[UUID] = None,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Generate sales report"""
        from server.models.inventory import InventoryItem
        
        stmt = (
            select(
                func.date(Transaction.created_at).label("date"),
                func.count(Transaction.id).label("transaction_count"),
                func.sum(Transaction.quantity).label("total_quantity"),
                func.sum(Transaction.total_price).label("total_sales"),
                func.count(func.distinct(Transaction.item_id)).label("unique_items"),
            )
            .join(InventoryItem, Transaction.item_id == InventoryItem.id)
            .where(Transaction.transaction_type == TransactionType.OUT)
            .where(Transaction.created_at >= start_date)
            .where(Transaction.created_at <= end_date)
        )
        
        if warehouse_id:
            stmt = stmt.where(InventoryItem.warehouse_id == warehouse_id)
        
        stmt = stmt.group_by(func.date(Transaction.created_at))
        result = await db.execute(stmt)
        daily_sales = result.all()
        
        # Calculate summary
        total_sales = sum(row.total_sales or 0 for row in daily_sales)
        total_quantity = sum(row.total_quantity or 0 for row in daily_sales)
        
        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "daily_sales": [
                {
                    "date": row.date,
                    "transaction_count": row.transaction_count,
                    "total_quantity": row.total_quantity,
                    "total_sales": row.total_sales,
                    "unique_items": row.unique_items,
                }
                for row in daily_sales
            ],
            "summary": {
                "total_transactions": sum(row.transaction_count for row in daily_sales),
                "total_quantity": total_quantity,
                "total_sales": total_sales,
                "average_daily_sales": total_sales / len(daily_sales) if daily_sales else 0,
            },
        }
    
    async def get_stock_movement(
        self,
        db: AsyncSession,
        *,
        item_id: UUID,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get stock movement history for an item"""
        from sqlalchemy.sql import case
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily stock levels
        stmt = (
            select(
                func.date(Transaction.created_at).label("date"),
                func.max(Transaction.new_stock).label("closing_stock"),
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.IN, Transaction.quantity),
                        else_=0,
                    )
                ).label("stock_in"),
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.OUT, Transaction.quantity),
                        else_=0,
                    )
                ).label("stock_out"),
            )
            .where(Transaction.item_id == item_id)
            .where(Transaction.created_at >= start_date)
            .where(Transaction.created_at <= end_date)
            .group_by(func.date(Transaction.created_at))
            .order_by(func.date(Transaction.created_at))
        )
        
        result = await db.execute(stmt)
        movement_data = result.all()
        
        return {
            "item_id": item_id,
            "period": {"days": days, "start_date": start_date, "end_date": end_date},
            "movement": [
                {
                    "date": row.date,
                    "closing_stock": row.closing_stock,
                    "stock_in": row.stock_in or 0,
                    "stock_out": row.stock_out or 0,
                }
                for row in movement_data
            ],
        }

class CRUDStockAlert(CRUDBase[StockAlert, Any, Any]):
    async def create_alert(
        self,
        db: AsyncSession,
        *,
        item_id: UUID,
        alert_type: str,
        current_stock: int,
        threshold: int,
    ) -> StockAlert:
        """Create a new stock alert"""
        from server.models.inventory import InventoryItem
        
        # Get item name
        stmt = select(InventoryItem.name).where(InventoryItem.id == item_id)
        result = await db.execute(stmt)
        item_name = result.scalar()
        
        # Create alert message
        messages = {
            "low_stock": f"Stok {item_name} hampir habis (stok: {current_stock}, minimal: {threshold})",
            "out_of_stock": f"Stok {item_name} sudah habis",
            "over_stock": f"Stok {item_name} melebihi batas maksimal (stok: {current_stock}, maksimal: {threshold})",
        }
        
        message = messages.get(alert_type, f"Alert untuk {item_name}")
        
        db_obj = StockAlert(
            item_id=item_id,
            alert_type=alert_type,
            current_stock=current_stock,
            threshold=threshold,
            message=message,
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_unread_alerts(
        self, db: AsyncSession, *, warehouse_id: Optional[UUID] = None
    ) -> List[StockAlert]:
        """Get unread alerts"""
        from server.models.inventory import InventoryItem
        
        stmt = (
            select(StockAlert)
            .join(InventoryItem, StockAlert.item_id == InventoryItem.id)
            .where(StockAlert.is_read == False)
        )
        
        if warehouse_id:
            stmt = stmt.where(InventoryItem.warehouse_id == warehouse_id)
        
        stmt = stmt.order_by(desc(StockAlert.created_at))
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def mark_as_read(
        self, db: AsyncSession, *, alert_id: UUID, user_id: UUID
    ) -> StockAlert:
        """Mark an alert as read"""
        alert = await self.get(db, id=alert_id)
        if not alert:
            raise ValueError("Alert not found")
        
        alert.is_read = True
        alert.read_by = user_id
        alert.read_at = datetime.utcnow()
        
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert
    
    async def get_recent_alerts(
        self, db: AsyncSession, *, days: int = 7, warehouse_id: Optional[UUID] = None
    ) -> List[StockAlert]:
        """Get recent alerts"""
        from server.models.inventory import InventoryItem
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = (
            select(StockAlert)
            .join(InventoryItem, StockAlert.item_id == InventoryItem.id)
            .where(StockAlert.created_at >= cutoff_date)
        )
        
        if warehouse_id:
            stmt = stmt.where(InventoryItem.warehouse_id == warehouse_id)
        
        stmt = stmt.order_by(desc(StockAlert.created_at))
        result = await db.execute(stmt)
        return result.scalars().all()

# Initialize CRUD instances
transaction = CRUDTransaction(Transaction)
stock_alert = CRUDStockAlert(StockAlert)