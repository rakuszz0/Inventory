import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

def generate_sku(category_code: str = "ITM") -> str:
    """Generate unique SKU."""
    timestamp = datetime.utcnow().strftime("%y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{category_code}-{timestamp}-{random_str}"

def generate_transaction_code() -> str:
    """Generate unique transaction code."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_uppercase, k=4))
    return f"TRX-{timestamp}-{random_str}"

def generate_api_key() -> str:
    """Generate API key."""
    random_bytes = random.getrandbits(256).to_bytes(32, 'big')
    return hashlib.sha256(random_bytes).hexdigest()

def calculate_age(birth_date: datetime) -> int:
    """Calculate age from birth date."""
    today = datetime.utcnow().date()
    age = today.year - birth_date.year
    
    # Adjust if birthday hasn't occurred yet this year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return age

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minutes"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} hours {minutes} minutes"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days} days {hours} hours"

def paginate_list(items: list, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """Paginate a list of items."""
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
        "has_next": end < total,
        "has_prev": page > 1,
    }

def safe_getattr(obj, attr: str, default=None):
    """Safely get attribute from object."""
    try:
        return getattr(obj, attr, default)
    except AttributeError:
        return default

def dict_to_query_params(params: Dict[str, Any]) -> str:
    """Convert dictionary to query parameters string."""
    return "&".join(f"{k}={v}" for k, v in params.items() if v is not None)