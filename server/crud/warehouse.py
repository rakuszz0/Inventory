from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from server.models.warehouse import Warehouse
from server.schemas.warehouse import WarehouseCreate, WarehouseUpdate
from server.crud.base import CRUDBase

class CRUDWarehouse(CRUDBase[Warehouse, WarehouseCreate, WarehouseUpdate]):
    async def get_with_items(
        self, db: AsyncSession, *, id: UUID
    ) -> Optional[Warehouse]:
        """Get warehouse with its items"""
        stmt = (
            select(Warehouse)
            .options(selectinload(Warehouse.inventory_items))
            .where(Warehouse.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_code(self, db: AsyncSession, *, code: str) -> Optional[Warehouse]:
        """Get warehouse by code"""
        stmt = select(Warehouse).where(Warehouse.code == code)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_active_warehouses(self, db: AsyncSession) -> List[Warehouse]:
        """Get all active warehouses"""
        stmt = select(Warehouse).where(Warehouse.is_active == True)
        result = await db.execute(stmt)
        return result.scalars().all()

# Initialize CRUD instance
warehouse = CRUDWarehouse(Warehouse)