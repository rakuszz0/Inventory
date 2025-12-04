# crud/inventory.py

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, case, text
from sqlalchemy.orm import selectinload

# Impor hanya model dan schema yang diperlukan untuk InventoryItem
from server.models.inventory import InventoryItem
from server.schemas.inventory import InventoryItemCreate, InventoryItemUpdate
from server.crud.base import CRUDBase

# HAPUS KELAS CRUDCategory dan CRUDWarehouse YANG DUPLIKAT DI SINI
# HAPUS juga inisiasi category dan warehouse di akhir file

class CRUDInventoryItem(CRUDBase[InventoryItem, InventoryItemCreate, InventoryItemUpdate]):
    async def get_with_details(
        self, db: AsyncSession, *, id: UUID
    ) -> Optional[InventoryItem]:
        """Get inventory item with related details"""
        stmt = (
            select(InventoryItem)
            .options(
                selectinload(InventoryItem.category),
                selectinload(InventoryItem.warehouse),
                selectinload(InventoryItem.creator),
            )
            .where(InventoryItem.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_sku(self, db: AsyncSession, *, sku: str) -> Optional[InventoryItem]:
        """Get inventory item by SKU"""
        stmt = select(InventoryItem).where(InventoryItem.sku == sku)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_barcode(
        self, db: AsyncSession, *, barcode: str
    ) -> Optional[InventoryItem]:
        """Get inventory item by barcode"""
        stmt = select(InventoryItem).where(InventoryItem.barcode == barcode)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_multi_by_warehouse(
        self, db: AsyncSession, *, warehouse_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[InventoryItem]:
        """Get inventory items by warehouse"""
        stmt = (
            select(InventoryItem)
            .where(InventoryItem.warehouse_id == warehouse_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_multi_filtered(
        self,
        db: AsyncSession,
        *,
        warehouse_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        min_stock: Optional[int] = None,
        max_stock: Optional[int] = None,
        is_active: Optional[bool] = True,  # Default to active only
        skip: int = 0,
        limit: int = 100,
    ) -> List[InventoryItem]:
        """Get filtered inventory items"""
        stmt = select(InventoryItem)
        
        # Apply filters
        filters = []
        if warehouse_id:
            filters.append(InventoryItem.warehouse_id == warehouse_id)
        if category_id:
            filters.append(InventoryItem.category_id == category_id)
        if min_stock is not None:
            filters.append(InventoryItem.current_stock >= min_stock)
        if max_stock is not None:
            filters.append(InventoryItem.current_stock <= max_stock)
        if is_active is not None:
            filters.append(InventoryItem.is_active == is_active)
        
        if filters:
            stmt = stmt.where(and_(*filters))
        
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_multi_filtered_with_count(
        self,
        db: AsyncSession,
        *,
        warehouse_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        min_stock: Optional[int] = None,
        max_stock: Optional[int] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[InventoryItem], int]:
        """Get filtered inventory items with total count for pagination"""
        # Build base query
        stmt = select(InventoryItem)
        count_stmt = select(func.count()).select_from(InventoryItem)
        
        # Apply filters
        filters = []
        if warehouse_id:
            filters.append(InventoryItem.warehouse_id == warehouse_id)
        if category_id:
            filters.append(InventoryItem.category_id == category_id)
        if min_stock is not None:
            filters.append(InventoryItem.current_stock >= min_stock)
        if max_stock is not None:
            filters.append(InventoryItem.current_stock <= max_stock)
        if is_active is not None:
            filters.append(InventoryItem.is_active == is_active)
        
        # Apply search filter
        if search:
            search_filters = [
                InventoryItem.name.ilike(f"%{search}%"),
                InventoryItem.sku.ilike(f"%{search}%"),
                InventoryItem.description.ilike(f"%{search}%") if InventoryItem.description is not None else False
            ]
            search_filter = or_(*[f for f in search_filters if f is not False])
            filters.append(search_filter)
        
        # Apply filters to both statements
        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))
        
        # Get total count
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # Get items with pagination
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        return items, total
    
    async def get_low_stock_items(
        self, db: AsyncSession, *, warehouse_id: Optional[UUID] = None
    ) -> List[InventoryItem]:
        """Get items with low stock (current_stock <= min_stock)"""
        stmt = select(InventoryItem).where(
            and_(
                InventoryItem.current_stock <= InventoryItem.min_stock,
                InventoryItem.current_stock > 0,  # Exclude out of stock
                InventoryItem.is_active == True
            )
        )
        
        if warehouse_id:
            stmt = stmt.where(InventoryItem.warehouse_id == warehouse_id)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_out_of_stock_items(
        self, db: AsyncSession, *, warehouse_id: Optional[UUID] = None
    ) -> List[InventoryItem]:
        """Get items that are out of stock"""
        stmt = select(InventoryItem).where(
            and_(
                InventoryItem.current_stock == 0,
                InventoryItem.is_active == True
            )
        )
        
        if warehouse_id:
            stmt = stmt.where(InventoryItem.warehouse_id == warehouse_id)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def update_stock(
        self, db: AsyncSession, *, item_id: UUID, new_stock: int
    ) -> InventoryItem:
        """Update item stock"""
        item = await self.get(db, id=item_id)
        if not item:
            raise ValueError("Item not found")
        
        if new_stock < 0:
            raise ValueError("Stock cannot be negative")
        
        item.current_stock = new_stock
        item.updated_at = datetime.utcnow()
        
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item
    
    async def adjust_stock(
        self, db: AsyncSession, *, item_id: UUID, adjustment: int
    ) -> InventoryItem:
        """Adjust stock (positive for increase, negative for decrease)"""
        item = await self.get(db, id=item_id)
        if not item:
            raise ValueError("Item not found")
        
        new_stock = item.current_stock + adjustment
        if new_stock < 0:
            raise ValueError("Insufficient stock")
        
        # Update stock
        item.current_stock = new_stock
        item.updated_at = datetime.utcnow()
        
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item
    
    async def get_inventory_summary(
        self, db: AsyncSession, *, warehouse_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get inventory summary statistics"""
        # Base query for summary
        query = select(
            func.count(InventoryItem.id).label("total_items"),
            func.sum(InventoryItem.current_stock).label("total_stock"),
            func.sum(
                case(
                    (InventoryItem.buy_price.isnot(None), 
                     InventoryItem.current_stock * InventoryItem.buy_price),
                    else_=0
                )
            ).label("total_value"),
            func.count(
                case(
                    (InventoryItem.current_stock == 0, 1),
                )
            ).label("out_of_stock_items"),
            func.count(
                case(
                    (
                        and_(
                            InventoryItem.current_stock > 0,
                            InventoryItem.current_stock <= InventoryItem.min_stock,
                        ),
                        1,
                    ),
                )
            ).label("low_stock_items"),
        ).where(InventoryItem.is_active == True)
        
        if warehouse_id:
            query = query.where(InventoryItem.warehouse_id == warehouse_id)
        
        result = await db.execute(query)
        summary = result.first()
        
        # Get categories summary
        # Note: This part requires Category model to be imported correctly in the model file
        from server.models.category import Category
        cat_query = (
            select(
                Category.name,
                func.count(InventoryItem.id).label("item_count"),
                func.sum(InventoryItem.current_stock).label("total_stock"),
                func.sum(
                    case(
                        (InventoryItem.buy_price.isnot(None),
                         InventoryItem.current_stock * InventoryItem.buy_price),
                        else_=0
                    )
                ).label("total_value"),
            )
            .join(InventoryItem, InventoryItem.category_id == Category.id)
            .where(InventoryItem.is_active == True)
        )
        
        if warehouse_id:
            cat_query = cat_query.where(InventoryItem.warehouse_id == warehouse_id)
        
        cat_query = cat_query.group_by(Category.id, Category.name)
        cat_result = await db.execute(cat_query)
        categories_summary = [
            {
                "name": row.name,
                "item_count": row.item_count,
                "total_stock": row.total_stock,
                "total_value": float(row.total_value) if row.total_value else 0.0,
            }
            for row in cat_result.all()
        ]
        
        return {
            "total_items": summary.total_items or 0,
            "total_stock": summary.total_stock or 0,
            "total_value": float(summary.total_value) if summary.total_value else 0.0,
            "out_of_stock_items": summary.out_of_stock_items or 0,
            "low_stock_items": summary.low_stock_items or 0,
            "categories_summary": categories_summary,
        }
    
    async def get_total_inventory_value(
        self,
        db: AsyncSession,
        *,
        warehouse_id: Optional[UUID] = None,
    ) -> float:
        """
        Calculate total inventory value.
        """
        query = select(
            func.sum(
                case(
                    (InventoryItem.buy_price.isnot(None),
                     InventoryItem.current_stock * InventoryItem.buy_price),
                    else_=0
                )
            )
        ).where(InventoryItem.is_active == True)
        
        if warehouse_id:
            query = query.where(InventoryItem.warehouse_id == warehouse_id)
        
        result = await db.execute(query)
        total_value = result.scalar()
        
        return float(total_value) if total_value else 0.0
    
    async def get_dashboard_stats(
        self,
        db: AsyncSession,
        *,
        warehouse_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get dashboard statistics.
        """
        stats = await self.get_inventory_summary(db, warehouse_id=warehouse_id)
        
        # Calculate average stock per item
        avg_stock = 0
        if stats["total_items"] > 0:
            avg_stock = stats["total_stock"] / stats["total_items"]
        
        # Calculate average value per item
        avg_value = 0
        if stats["total_items"] > 0:
            avg_value = stats["total_value"] / stats["total_items"]
        
        # Get top 5 items by value
        top_items_query = (
            select(
                InventoryItem.name,
                InventoryItem.current_stock,
                InventoryItem.buy_price,
                (InventoryItem.current_stock * InventoryItem.buy_price).label("item_value")
            )
            .where(InventoryItem.is_active == True)
            .order_by(text("item_value DESC"))
            .limit(5)
        )
        
        if warehouse_id:
            top_items_query = top_items_query.where(InventoryItem.warehouse_id == warehouse_id)
        
        top_items_result = await db.execute(top_items_query)
        top_items = [
            {
                "name": row.name,
                "stock": row.current_stock,
                "buy_price": float(row.buy_price) if row.buy_price else 0.0,
                "item_value": float(row.item_value) if row.item_value else 0.0,
            }
            for row in top_items_result.all()
        ]
        
        return {
            **stats,
            "avg_stock_per_item": round(avg_stock, 2),
            "avg_value_per_item": round(avg_value, 2),
            "top_items_by_value": top_items,
        }

# Initialize CRUD instance
inventory_item = CRUDInventoryItem(InventoryItem)