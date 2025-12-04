from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt

from server.core.config import settings

# KEEP pwd_context untuk compatibility
pwd_context = CryptContext(schemes=["bcrypt", "bcrypt-sha256"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password with multiple methods.
    Priority:
    1. bcrypt library (for $2b$... format)
    2. bcrypt-sha256 format ($bcrypt-sha256$...)
    3. passlib context (fallback)
    """
    try:
        # Method 1: bcrypt library (for standard bcrypt)
        if hashed_password.startswith("$2b$"):
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        
        # Method 2: Handle bcrypt-sha256 format
        if hashed_password.startswith("$bcrypt-sha256$"):
            # Format: $bcrypt-sha256$v=2,t=2b,r=12$...$...
            parts = hashed_password.split('$')
            if len(parts) >= 5:
                # Extract bcrypt part
                bcrypt_hash = "$" + "$".join(parts[4:])
                return bcrypt.checkpw(
                    plain_password.encode('utf-8'),
                    bcrypt_hash.encode('utf-8')
                )
        
        # Method 3: Fallback to passlib
        return pwd_context.verify(plain_password, hashed_password)
        
    except Exception as e:
        print(f"DEBUG verify_password error: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """Hash password dengan bcrypt standard"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# JWT functions
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None