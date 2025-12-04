# crud/category.py

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from server.models.category import Category
from server.schemas.category import CategoryCreate, CategoryUpdate
from server.crud.base import CRUDBase

class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    async def get_with_items(
        self, db: AsyncSession, *, id: UUID
    ) -> Optional[Category]:
        """Get category with its items"""
        stmt = (
            select(Category)
            .options(
                selectinload(Category.inventory_items),
                selectinload(Category.parent),
                selectinload(Category.subcategories)
            )
            .where(Category.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get(self, db: AsyncSession, *, id: UUID) -> Optional[Category]:
        """Get category by ID without loading relationships"""
        stmt = select(Category).where(Category.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Category]:
        """Get category by name"""
        stmt = select(Category).where(Category.name == name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_hierarchy(self, db: AsyncSession) -> List[Category]:
        """Get categories hierarchy (with parent-child relationships)"""
        stmt = (
            select(Category)
            .where(Category.parent_id == None)
            .options(
                selectinload(Category.subcategories).selectinload(Category.subcategories)
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()

# Initialize CRUD instance
category = CRUDCategory(Category)