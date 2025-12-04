"""
API module for Inventory Management System.
"""

from .v1 import (
    auth_router,
    users_router,
    warehouses_router,
    categories_router,
    inventory_router,
    transactions_router,
    reports_router,
)

__all__ = [
    "auth_router",
    "users_router",
    "warehouses_router", 
    "categories_router",
    "inventory_router",
    "transactions_router",
    "reports_router",
]