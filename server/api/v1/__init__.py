from .auth import router as auth_router
from .users import router as users_router
from .warehouses import router as warehouses_router
from .categories import router as categories_router
from .inventory import router as inventory_router
from .transactions import router as transactions_router
from .reports import router as reports_router

__all__ = [
    "auth_router",
    "users_router",
    "warehouses_router",
    "categories_router",
    "inventory_router",
    "transactions_router",
    "reports_router",
]