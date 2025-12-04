from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError 
from starlette.middleware.base import BaseHTTPMiddleware
from server.core.config import settings
from server.crud.user import user

security = HTTPBearer()

class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware to validate JWT tokens"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for certain paths
        public_paths = [
            "/docs", "/redoc", "/openapi.json",
            "/api/v1/auth/login", "/api/v1/auth/register",
            "/api/v1/auth/refresh", "/health"
        ]
        
        if request.url.path in public_paths:
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        try:
            # Extract token
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Decode token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check token type
            token_type = payload.get("type")
            if token_type != "access":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token type",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Get user info
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Store user info in request state
            request.state.user_id = user_id
            request.state.user_role = payload.get("role", "guest")
            request.state.user_email = payload.get("email")
            request.state.warehouse_id = payload.get("warehouse_id")
            
        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Continue with the request
        return await call_next(request)


# JIKA INI DEPENDENCY (sebaiknya pindah ke deps.py atau biarkan sebagai fungsi):
"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from server.core.config import settings
from server.crud.user import user

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_obj = await user.get(user_id)
    if user_obj is None:
        raise credentials_exception
    
    return user_obj

async def require_role(role: str):
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(
                status_code=403,
                detail=f"Requires {role} role"
            )
        return current_user
    return role_checker
"""