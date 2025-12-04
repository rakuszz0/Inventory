# schemas/__init__.py

# Import all schemas from their respective modules
from server.schemas.user import *
from server.schemas.warehouse import *
from server.schemas.category import *
from server.schemas.inventory import *
from server.schemas.transactions import *
from server.schemas.common import *

# Rebuild all models with forward references
# This ensures all cross-references between schemas are resolved correctly
UserResponse.model_rebuild()
UserDetailResponse.model_rebuild()

WarehouseResponse.model_rebuild()
WarehouseDetailResponse.model_rebuild()
WarehouseWithStats.model_rebuild()

CategoryResponse.model_rebuild()
CategoryDetailResponse.model_rebuild()
CategoryTreeResponse.model_rebuild()
CategoryWithStats.model_rebuild()

InventoryItemResponse.model_rebuild()
InventoryItemDetailResponse.model_rebuild()
PaginatedInventoryResponse.model_rebuild()

TransactionResponse.model_rebuild()
TransactionDetailResponse.model_rebuild()

# No need for try-except blocks as all schemas should be properly defined now