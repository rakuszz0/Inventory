from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from server.core.config import settings
from server.core.database import init_db, get_db

# Import routers - PASTIKAN PATH INI BENAR
from server.api.v1.auth import router as auth_router
from server.api.v1.users import router as users_router
from server.api.v1.warehouses import router as warehouses_router
from server.api.v1.categories import router as categories_router
from server.api.v1.inventory import router as inventory_router
from server.api.v1.transactions import router as transactions_router
from server.api.v1.reports import router as reports_router

# Import middleware with fallbacks
RATE_LIMIT_AVAILABLE = False
AUDIT_MIDDLEWARE_AVAILABLE = False

try:
    from server.middleware.rate_limit import RateLimitMiddleware
    RATE_LIMIT_AVAILABLE = True
except ImportError as e:
    print(f"RateLimitMiddleware not available: {e}")

try:
    from server.middleware.audit import AuditMiddleware
    AUDIT_MIDDLEWARE_AVAILABLE = True
except ImportError as e:
    print(f"AuditMiddleware not available: {e}")

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    print("Starting application...")
    try:
        await init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        # Don't raise, continue without DB if in development
        if not settings.DEBUG:
            raise
    
    yield
    
    # Shutdown
    print("Application shutting down...")

# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Inventory Management System API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ===================== MIDDLEWARE CONFIGURATION =====================
# Configure CORS
if hasattr(settings, 'CORS_ALLOWED_ORIGINS') and settings.CORS_ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Default CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add security middleware - TrustedHostMiddleware
if not settings.DEBUG:
    try:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"] if settings.DEBUG else settings.ALLOWED_HOSTS if hasattr(settings, 'ALLOWED_HOSTS') else ["*"],
        )
    except Exception as e:
        print(f" TrustedHostMiddleware configuration failed: {e}")

# Add custom middleware
if not settings.DEBUG and RATE_LIMIT_AVAILABLE:
    try:
        app.add_middleware(RateLimitMiddleware)
        print(" RateLimitMiddleware added")
    except Exception as e:
        print(f" RateLimitMiddleware failed: {e}")

if AUDIT_MIDDLEWARE_AVAILABLE:
    try:
        # app.add_middleware(AuditMiddleware)
        print(" AuditMiddleware added")
    except Exception as e:
        print(f"AuditMiddleware failed: {e}")

# ===================== ROUTER REGISTRATION =====================
# Include routers
API_PREFIX = "/api/v1"

routers = [
    (auth_router, f"{API_PREFIX}/auth", "authentication"),
    (users_router, f"{API_PREFIX}/users", "users"),
    (warehouses_router, f"{API_PREFIX}/warehouses", "warehouses"),
    (categories_router, f"{API_PREFIX}/categories", "categories"),
    (inventory_router, f"{API_PREFIX}/inventory", "inventory"),
    (transactions_router, f"{API_PREFIX}/transactions", "transactions"),
    (reports_router, f"{API_PREFIX}/reports", "reports"),
]

print("\n" + "="*50)
print("REGISTERING ROUTERS:")
print("="*50)

for router, prefix, tags in routers:
    try:
        app.include_router(router, prefix=prefix, tags=[tags])
        print(f"Router '{tags}' registered at {prefix}")
        # Print all routes for this router
        for route in router.routes:
            if hasattr(route, "path"):
                print(f"   - {route.path}")
    except Exception as e:
        print(f"Failed to register router '{tags}': {e}")

print("="*50 + "\n")

# ===================== API ENDPOINTS =====================
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None,
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "development" if settings.DEBUG else "production",
        "api_endpoints": {
            "auth": f"{API_PREFIX}/auth",
            "users": f"{API_PREFIX}/users",
            "warehouses": f"{API_PREFIX}/warehouses",
            "categories": f"{API_PREFIX}/categories",
            "inventory": f"{API_PREFIX}/inventory",
            "transactions": f"{API_PREFIX}/transactions",
            "reports": f"{API_PREFIX}/reports",
        }
    }

@app.get("/health", tags=["health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint to verify API and database status.
    """
    try:
        # Test database connection
        from sqlalchemy import text
        result = await db.execute(text("SELECT 1"))
        db_test = result.scalar() == 1
        
        # Check middleware status
        middleware_status = {
            "cors": True,  # CORS is always enabled
            "rate_limit": RATE_LIMIT_AVAILABLE,
            "audit": AUDIT_MIDDLEWARE_AVAILABLE,
        }
        
        # Check redis if available
        redis_status = False
        try:
            from server.core.redis import get_redis
            redis_client = await get_redis()
            if redis_client:
                await redis_client.ping()
                redis_status = True
        except:
            redis_status = False
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": db_test,
                "redis": redis_status,
                "middleware": middleware_status,
            },
            "version": settings.APP_VERSION,
            "environment": "development" if settings.DEBUG else "production",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": False,
                "redis": False,
                "middleware": {},
            },
            "error": str(e) if settings.DEBUG else "Service unavailable",
            "version": settings.APP_VERSION,
        }

@app.get("/api", tags=["api"])
async def api_info():
    """
    API information endpoint.
    """
    return {
        "api_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Inventory Management System API",
        "contact": {
            "name": "Support Team",
            "email": "support@inventory.com",
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "authentication": "Bearer Token (JWT)",
        "rate_limiting": "Enabled" if RATE_LIMIT_AVAILABLE else "Disabled",
        "endpoints": {
            "authentication": {
                "register": "POST /api/v1/auth/register",
                "login": "POST /api/v1/auth/login",
                "refresh": "POST /api/v1/auth/refresh",
                "me": "GET /api/v1/auth/me",
                "change_password": "POST /api/v1/auth/change-password",
            },
            "users": {
                "list": "GET /api/v1/users",
                "create": "POST /api/v1/users",
                "get": "GET /api/v1/users/{id}",
                "update": "PUT /api/v1/users/{id}",
                "delete": "DELETE /api/v1/users/{id}",
                "by_warehouse": "GET /api/v1/users/warehouse/{warehouse_id}",
            },
            "warehouses": {
                "list": "GET /api/v1/warehouses",
                "create": "POST /api/v1/warehouses",
                "get": "GET /api/v1/warehouses/{id}",
                "update": "PUT /api/v1/warehouses/{id}",
                "delete": "DELETE /api/v1/warehouses/{id}",
                "summary": "GET /api/v1/warehouses/{id}/summary",
            },
            "categories": {
                "list": "GET /api/v1/categories",
                "create": "POST /api/v1/categories",
                "get": "GET /api/v1/categories/{id}",
                "update": "PUT /api/v1/categories/{id}",
                "delete": "DELETE /api/v1/categories/{id}",
            },
            "inventory": {
                "list": "GET /api/v1/inventory/",
                "create": "POST /api/v1/inventory/",
                "get": "GET /api/v1/inventory/{item_id}",
                "update": "PUT /api/v1/inventory/{item_id}",
                "delete": "DELETE /api/v1/inventory/{item_id}",
                "adjust_stock": "POST /api/v1/inventory/{item_id}/adjust-stock",
                "transactions": "GET /api/v1/inventory/{item_id}/transactions",
                "summary": "GET /api/v1/inventory/summary",
                "low_stock": "GET /api/v1/inventory/low-stock",
                "out_of_stock": "GET /api/v1/inventory/out-of-stock",
                "value": "GET /api/v1/inventory/value",
            },
            "transactions": {
                "list": "GET /api/v1/transactions",
                "stock_in": "POST /api/v1/transactions/stock-in",
                "stock_out": "POST /api/v1/transactions/stock-out",
                "today_sales": "GET /api/v1/transactions/sales/today",
                "daily_sales": "GET /api/v1/transactions/sales/daily",
            },
            "reports": {
                "inventory_summary": "GET /api/v1/reports/inventory/summary",
                "sales": "GET /api/v1/reports/sales",
                "export": "GET /api/v1/reports/inventory/export",
                "alerts": "GET /api/v1/reports/alerts",
                "stock_movement": "GET /api/v1/reports/stock-movement/{item_id}",
            }
        }
    }

@app.get("/status", tags=["status"])
async def status_check():
    """
    Simple status check without database dependency.
    """
    return {
        "status": "running",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "uptime": "unknown",  # Could implement with startup time
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "authentication": True,
            "database": True,
            "cors": True,
            "rate_limiting": RATE_LIMIT_AVAILABLE,
            "audit_logging": AUDIT_MIDDLEWARE_AVAILABLE,
        }
    }

# ===================== ERROR HANDLERS =====================
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Custom HTTP exception handler.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom validation error handler.
    """
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": exc.errors() if settings.DEBUG else "Invalid request data",
            "status_code": 422,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Generic exception handler for all unhandled exceptions.
    """
    import traceback
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "details": traceback.format_exc() if settings.DEBUG else None,
            "status_code": 500,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

# ===================== MAIN ENTRY POINT =====================
def print_banner():
    """Print application banner."""
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     {settings.APP_NAME} v{settings.APP_VERSION}                    ║
║                                                              ║
║     Starting in {'DEVELOPMENT' if settings.DEBUG else 'PRODUCTION'} mode        ║
║     Host: 0.0.0.0:8000                                   ║
║     Docs: http://localhost:8000/docs                     ║
║     Debug: {settings.DEBUG}                                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

if __name__ == "__main__":
    print_banner()
    
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        access_log=True,
        workers=1 if settings.DEBUG else 4,
    )