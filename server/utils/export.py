import csv
import io
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from server.schemas.inventory import InventoryItemResponse
from server.schemas.transactions import TransactionResponse

async def export_inventory_to_csv(items: List[InventoryItemResponse]) -> io.StringIO:
    """
    Export inventory items to CSV format.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'SKU', 'Barcode', 'Name', 'Category', 'Warehouse',
        'Current Stock', 'Min Stock', 'Max Stock', 'Reorder Point',
        'Buy Price', 'Sell Price', 'Profit Margin (%)', 'Total Value', 
        'Stock Status', 'Unit', 'Is Active',
        'Created At', 'Last Updated', 'Last Restocked', 'Last Sold'
    ])
    
    # Write data
    for item in items:
        writer.writerow([
            item.sku,
            item.barcode or '',
            item.name,
            item.category.name if item.category else '',
            item.warehouse.name if item.warehouse else '',
            item.current_stock,
            item.min_stock,
            item.max_stock or '',
            item.reorder_point or '',
            f"{item.buy_price:.2f}",
            f"{item.sell_price:.2f}",
            f"{item.profit_margin:.2f}" if hasattr(item, 'profit_margin') else '',
            f"{item.total_value:.2f}" if hasattr(item, 'total_value') else '',
            item.stock_status if hasattr(item, 'stock_status') else '',
            item.unit,
            'Yes' if item.is_active else 'No',
            item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else '',
            item.last_restocked_at.strftime('%Y-%m-%d %H:%M:%S') if item.last_restocked_at else '',
            item.last_sold_at.strftime('%Y-%m-%d %H:%M:%S') if item.last_sold_at else '',
        ])
    
    output.seek(0)
    return output

async def export_transactions_to_csv(transactions: List[TransactionResponse]) -> io.StringIO:
    """
    Export transactions to CSV format.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Transaction Code', 'Date', 'Item SKU', 'Item Name',
        'Transaction Type', 'Quantity', 'Unit Price', 'Total Price',
        'Previous Stock', 'New Stock', 'Reference', 'Notes',
        'Created By', 'Warehouse'
    ])
    
    # Write data
    for tx in transactions:
        writer.writerow([
            tx.transaction_code,
            tx.created_at.strftime('%Y-%m-%d %H:%M:%S') if tx.created_at else '',
            tx.item.sku if tx.item else '',
            tx.item.name if tx.item else '',
            tx.transaction_type,
            tx.quantity,
            f"{tx.unit_price:.2f}" if tx.unit_price else '',
            f"{tx.total_price:.2f}" if tx.total_price else '',
            tx.previous_stock,
            tx.new_stock,
            tx.reference or '',
            tx.notes or '',
            tx.user.username if tx.user else '',
            tx.item.warehouse.name if tx.item and tx.item.warehouse else '',
        ])
    
    output.seek(0)
    return output

async def generate_inventory_report(
    db: AsyncSession,
    warehouse_id: Optional[UUID] = None,
    format: str = 'csv'
) -> Dict[str, Any]:
    """
    Generate inventory report.
    """
    from server import crud
    
    # Get summary
    summary = await crud.inventory_item.get_inventory_summary(
        db, warehouse_id=warehouse_id
    )
    
    # Get items with filters
    if warehouse_id:
        items = await crud.inventory_item.get_multi_by_warehouse(
            db, warehouse_id=warehouse_id, limit=5000
        )
    else:
        items = await crud.inventory_item.get_multi(db, limit=5000)
    
    # Convert to response schema
    from server.schemas.inventory import InventoryItemResponse
    item_responses = [
        InventoryItemResponse.from_orm(item) for item in items
    ]
    
    # Add relationships if needed
    for item_resp, item_orm in zip(item_responses, items):
        if hasattr(item_orm, 'warehouse') and item_orm.warehouse:
            from server.schemas.inventory import WarehouseResponse
            item_resp.warehouse = WarehouseResponse.from_orm(item_orm.warehouse)
        if hasattr(item_orm, 'category') and item_orm.category:
            from server.schemas.inventory import CategoryResponse
            item_resp.category = CategoryResponse.from_orm(item_orm.category)
    
    # Generate report based on format
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    if format == 'csv':
        csv_data = await export_inventory_to_csv(item_responses)
        return {
            "format": "csv",
            "data": csv_data.getvalue(),
            "filename": f"inventory_report_{timestamp}.csv",
            "summary": summary,
            "total_items": len(items),
            "generated_at": datetime.utcnow().isoformat(),
        }
    else:
        return {
            "format": "json",
            "items": [item.dict() for item in item_responses],
            "summary": summary,
            "total_items": len(items),
            "generated_at": datetime.utcnow().isoformat(),
        }

async def generate_sales_report(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    warehouse_id: Optional[UUID] = None,
    format: str = 'csv'
) -> Dict[str, Any]:
    """
    Generate sales report.
    """
    from server import crud
    
    # Get sales report
    report = await crud.transaction.get_sales_report(
        db,
        warehouse_id=warehouse_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    # Get detailed transactions
    transactions = await crud.transaction.get_by_warehouse(
        db,
        warehouse_id=warehouse_id,
        start_date=start_date,
        end_date=end_date,
        limit=1000,
    )
    
    # Convert to response schema
    from server.schemas.transactions import TransactionResponse
    transaction_responses = [
        TransactionResponse.from_orm(tx) for tx in transactions
    ]
    
    # Add relationships
    for tx_resp, tx_orm in zip(transaction_responses, transactions):
        if hasattr(tx_orm, 'item') and tx_orm.item:
            from server.schemas.inventory import InventoryItemResponse
            tx_resp.item = InventoryItemResponse.from_orm(tx_orm.item)
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    if format == 'csv':
        csv_data = await export_transactions_to_csv(transaction_responses)
        return {
            "format": "csv",
            "data": csv_data.getvalue(),
            "filename": f"sales_report_{timestamp}.csv",
            "summary": report.get('summary', {}),
            "period": report.get('period', {}),
            "total_transactions": len(transactions),
            "generated_at": datetime.utcnow().isoformat(),
        }
    else:
        return {
            "format": "json",
            "transactions": [tx.dict() for tx in transaction_responses],
            "summary": report.get('summary', {}),
            "period": report.get('period', {}),
            "total_transactions": len(transactions),
            "generated_at": datetime.utcnow().isoformat(),
        }

def format_currency(value: float) -> str:
    """Format currency value."""
    return f"Rp{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_percentage(value: float) -> str:
    """Format percentage value."""
    return f"{value:.2f}%"