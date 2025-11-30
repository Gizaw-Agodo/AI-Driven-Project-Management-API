from fastapi import APIRouter

from app.api.v1.endpoints import user, projects, tasks


# 🎓 ROUTER AGGREGATION
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    user.router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["projects"]
)

api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks"]
)