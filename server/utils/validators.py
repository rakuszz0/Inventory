import re
from typing import Optional
from uuid import UUID
from datetime import datetime, date

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    # Basic Indonesian phone number validation
    pattern = r'^(\+62|62|0)[0-9]{9,13}$'
    return bool(re.match(pattern, phone))

def validate_sku(sku: str) -> bool:
    """Validate SKU format."""
    # Alphanumeric with hyphens, 3-50 characters
    pattern = r'^[A-Za-z0-9-]{3,50}$'
    return bool(re.match(pattern, sku))

def validate_barcode(barcode: str) -> bool:
    """Validate barcode format."""
    # Common barcode formats (EAN-13, UPC, etc.)
    if len(barcode) not in [8, 12, 13, 14]:
        return False
    
    # Check if all characters are digits
    return barcode.isdigit()

def validate_price(price: float) -> bool:
    """Validate price."""
    return price >= 0

def validate_stock(stock: int) -> bool:
    """Validate stock quantity."""
    return stock >= 0

def validate_date_range(start_date: date, end_date: date) -> bool:
    """Validate date range."""
    return start_date <= end_date

def validate_uuid(value: str) -> bool:
    """Validate UUID format."""
    try:
        UUID(value)
        return True
    except ValueError:
        return False

def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input."""
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if max_length specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"
    
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    
    return True, "Password is strong"