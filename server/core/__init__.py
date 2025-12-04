"""
Core module for the Inventory Management System.
"""

from .config import Settings, get_settings, settings
from .database import engine, AsyncSessionLocal, Base, get_db, init_db
from .security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    pwd_context
)

__all__ = [
    "Settings",
    "get_settings",
    "settings",
    "engine",
    "AsyncSessionLocal",
    "Base",
    "get_db",
    "init_db",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "pwd_context",
]

# Optional: Function to create default admin
async def create_default_admin(session):
    """Create default admin user if not exists"""
    from server.models.user import User
    from server.crud.user import user
    
    admin_email = "admin@example.com"
    existing_admin = await user.get_by_email(session, email=admin_email)
    
    if not existing_admin:
        admin_user = User(
            username="admin",
            email=admin_email,
            password_hash=get_password_hash("admin123"),  # Change in production!
            role="super_admin",
            is_active=True,
            full_name="System Administrator"
        )
        session.add(admin_user)
        await session.commit()