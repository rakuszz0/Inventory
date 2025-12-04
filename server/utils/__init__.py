"""
Utility functions for Inventory Management System.
"""

from .alert import (
    check_stock_alerts,
    check_all_stock_alerts,
    mark_alerts_as_read,
    get_unread_alerts_count,
)
from .export import (
    export_inventory_to_csv,
    export_transactions_to_csv,
    generate_inventory_report,
    generate_sales_report,
    format_currency,
    format_percentage,
)
from .validators import (
    validate_email,
    validate_phone,
    validate_sku,
    validate_barcode,
    validate_price,
    validate_stock,
    validate_date_range,
    validate_uuid,
    sanitize_string,
    validate_password_strength,
)
from .helpers import (
    generate_sku,
    generate_transaction_code,
    generate_api_key,
    calculate_age,
    format_duration,
    paginate_list,
    safe_getattr,
    dict_to_query_params,
)

__all__ = [
    # Alert utilities
    "check_stock_alerts",
    "check_all_stock_alerts", 
    "mark_alerts_as_read",
    "get_unread_alerts_count",
    
    # Export utilities
    "export_inventory_to_csv",
    "export_transactions_to_csv",
    "generate_inventory_report",
    "generate_sales_report",
    "format_currency",
    "format_percentage",
    
    # Validation utilities
    "validate_email",
    "validate_phone", 
    "validate_sku",
    "validate_barcode",
    "validate_price",
    "validate_stock",
    "validate_date_range",
    "validate_uuid",
    "sanitize_string",
    "validate_password_strength",
    
    # Helper utilities
    "generate_sku",
    "generate_transaction_code",
    "generate_api_key",
    "calculate_age",
    "format_duration",
    "paginate_list",
    "safe_getattr",
    "dict_to_query_params",
]