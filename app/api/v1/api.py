from fastapi import APIRouter

from app.api.v1.endpoints import user


api_router = APIRouter()

# Include  routes
api_router.include_router( user.router, prefix="/users", tags=["users"] )
