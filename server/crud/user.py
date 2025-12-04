from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, update
from datetime import datetime

from server.models.user import User, UserRole
from server.schemas.user import UserCreate, UserUpdate
from server.core.security import get_password_hash, verify_password
from server.crud.base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate(
        self, db: AsyncSession, *, username: str, password: str
    ) -> Optional[User]:
        """Authenticate user"""
        stmt = select(User).where(
            or_(User.username == username, User.email == username)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            print(f"DEBUG: User '{username}' not found")
            return None
        
        print(f"DEBUG: Found user: {user.email}, password_hash: {user.password_hash[:30]}..." if user.password_hash else "DEBUG: No password_hash!")
        
        if not user.password_hash:
            print("DEBUG: password_hash is empty!")
            return None
        
        try:
            # Verifikasi password dengan bcrypt
            if verify_password(password, user.password_hash):
                print("DEBUG: Password verification SUCCESS")
                return user
            else:
                print("DEBUG: Password verification FAILED")
                return None
        except Exception as e:
            print(f"DEBUG: Verification error: {str(e)}")
            # Fallback untuk development: jika password masih plain text
            if password == user.password_hash:
                print("DEBUG: Plain text password match - migrating to hash")
                # Hash password baru
                user.password_hash = get_password_hash(password)
                # Tidak perlu commit di sini, biarkan caller yang menentukan
                return user
            return None

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Create new user with hashed password"""
        # Check existing email
        existing_user = await self.get_by_email(db, email=obj_in.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Check existing username
        existing_user = await self.get_by_username(db, username=obj_in.username)
        if existing_user:
            raise ValueError("User with this username already exists")

        # Hash password
        hashed_password = get_password_hash(obj_in.password)
        print(f"DEBUG: Creating user with hash: {hashed_password[:30]}...")
        
        # Create user dengan field yang benar
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            full_name=obj_in.full_name,
            password_hash=hashed_password,  # ← FIELD NAME YANG BENAR
            role=obj_in.role,
            warehouse_id=obj_in.warehouse_id,
            is_active=True,
            is_verified=False,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        print(f"DEBUG: User created: {db_obj.email}")
        return db_obj

    async def update_last_login(self, db: AsyncSession, *, user_id: UUID):
        """Update user's last login timestamp"""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_login=func.now())
            .returning(User)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()

    async def get_by_warehouse(
        self, db: AsyncSession, *, warehouse_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """Get users by warehouse"""
        stmt = (
            select(User)
            .where(User.warehouse_id == warehouse_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_active_users(self, db: AsyncSession) -> List[User]:
        """Get all active users"""
        stmt = select(User).where(User.is_active == True)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def update_password(
        self, db: AsyncSession, *, db_obj: User, new_password: str
    ) -> User:
        """Update user password"""
        hashed_password = get_password_hash(new_password)
        db_obj.password_hash = hashed_password
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def create_or_reset_admin(self, db: AsyncSession) -> User:
        """Create or reset admin user"""
        admin_email = "admin@example.com"
        admin_user = await self.get_by_email(db, email=admin_email)
        
        if admin_user:
            print(f"DEBUG: Admin user exists, resetting password")
            # Reset password
            admin_user.password_hash = get_password_hash("Admin@123")
            await db.commit()
            await db.refresh(admin_user)
            return admin_user
        else:
            print(f"DEBUG: Creating new admin user")
            # Create new admin
            admin_data = UserCreate(
                email=admin_email,
                username="admin",
                full_name="System Administrator",
                password="Admin@123",
                role=UserRole.SUPER_ADMIN,
                warehouse_id=None,
            )
            return await self.create(db, obj_in=admin_data)


# Instance CRUD
user = CRUDUser(User)


async def create_default_admin(db: AsyncSession):
    """Create default admin user if not exists"""
    admin_email = "admin@inventory.com"
    admin_user = await user.get_by_email(db, email=admin_email)

    if not admin_user:
        admin_data = UserCreate(
            email=admin_email,
            username="admin",
            full_name="Super Administrator",
            password="Admin123!",
            role=UserRole.SUPER_ADMIN,
        )

        await user.create(db, obj_in=admin_data)
        print("Default admin user created")
    else:
        print("Admin user already exists")