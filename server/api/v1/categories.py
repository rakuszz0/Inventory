# api/v1/categories.py

from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from server import crud, schemas
from server.api.v1 import deps
from server.models.user import UserRole
from typing import Optional

# --- PERBAIKAN: Hapus prefix untuk menghindari duplikasi URL ---
router = APIRouter(tags=["categories"])

@router.post("/", response_model=schemas.CategoryResponse)
async def create_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_in: schemas.CategoryCreate,
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Create new category.
    """
    # Only super admin can create categories
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can create categories",
        )
    
    try:
        # Check if category already exists
        existing_category = await crud.category.get_by_name(db, name=category_in.name)
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists",
            )
        
        # Check parent category if provided
        if category_in.parent_id:
            parent_category = await crud.category.get(db, id=category_in.parent_id)
            if not parent_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent category not found",
                )
        
        # Create category
        category = await crud.category.create(db, obj_in=category_in)

        # --- PERBAIKAN: Refresh dan muat relasi dengan aman ---
        await db.refresh(category)
        complete_category = await crud.category.get_with_items(db, id=category.id)
        
        return complete_category
    except Exception as e:
        # --- PERBAIKAN: Tangani error dengan lebih baik ---
        print(f"ERROR in create_category: {str(e)}") # Logging untuk debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/", response_model=List[schemas.CategoryResponse])
async def read_categories(
    *,
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_inactive: bool = Query(False),
) -> Any:
    """
    Retrieve categories.
    """
    try:
        # --- PERBAIKAN: Gunakan fungsi CRUD yang ada dan lebih sederhana ---
        categories = await crud.category.get_multi(db, skip=skip, limit=limit)
        
        if not include_inactive:
            categories = [cat for cat in categories if cat.is_active]
        
        return categories
    except Exception as e:
        print(f"ERROR in read_categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve categories: {str(e)}"
        )

@router.get("/hierarchy", response_model=List[schemas.CategoryResponse])
async def read_categories_hierarchy(
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Retrieve categories hierarchy.
    """
    try:
        categories = await crud.category.get_hierarchy(db)
        return categories
    except Exception as e:
        print(f"ERROR in read_categories_hierarchy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve category hierarchy: {str(e)}"
        )

@router.get("/{category_id}", response_model=schemas.CategoryResponse)
async def read_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_id: UUID,
) -> Any:
    """
    Get category by ID.
    """
    try:
        category = await crud.category.get_with_items(db, id=category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        return category
    except Exception as e:
        print(f"ERROR in read_category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve category: {str(e)}"
        )

@router.put("/{category_id}", response_model=schemas.CategoryResponse)
async def update_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_id: UUID,
    category_in: schemas.CategoryUpdate,
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Update category.
    """
    # Only super admin can update categories
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can update categories",
        )
    
    try:
        category = await crud.category.get(db, id=category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        
        # Check if name already exists (if changing name)
        if category_in.name and category_in.name != category.name:
            existing_category = await crud.category.get_by_name(db, name=category_in.name)
            if existing_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category with this name already exists",
                )
        
        # Check parent category if provided
        if category_in.parent_id:
            if category_in.parent_id == category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category cannot be its own parent",
                )
            
            parent_category = await crud.category.get(db, id=category_in.parent_id)
            if not parent_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent category not found",
                )
        
        category = await crud.category.update(db, db_obj=category, obj_in=category_in)
        
        # --- PERBAIKAN: Refresh dan muat relasi ---
        await db.refresh(category)
        complete_category = await crud.category.get_with_items(db, id=category.id)
        
        return complete_category
    except Exception as e:
        print(f"ERROR in update_category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update category: {str(e)}"
        )

@router.delete("/{category_id}")
async def delete_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_id: UUID,
    current_user: schemas.UserInDB = Depends(deps.get_current_user),
) -> Any:
    """
    Delete category.
    """
    # Only super admin can delete categories
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can delete categories",
        )
    
    try:
        category = await crud.category.get_with_items(db, id=category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        
        # Check if category has items
        if category.inventory_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category that has items",
                )
        
        # Check if category has subcategories
        if category.subcategories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category that has subcategories",
                )
        
        await crud.category.delete(db, id=category_id)
        return {"message": "Category deleted successfully"}
    except Exception as e:
        print(f"ERROR in delete_category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete category: {str(e)}"
        )