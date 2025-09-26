from fastapi import APIRouter
from .endpoints import leave_management, leave_admin, leave_validation

# Create the main API router for v1
api_router = APIRouter()

# Include leave management endpoints
api_router.include_router(leave_management.router)

# Include leave admin endpoints  
api_router.include_router(leave_admin.router)

# Include leave validation endpoints
api_router.include_router(leave_validation.router)

__all__ = ["api_router"]
