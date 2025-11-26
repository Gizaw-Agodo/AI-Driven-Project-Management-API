from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, Path, Body
from datetime import datetime

from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectWithTasks,
    ProjectStatusUpdate,
    ProjectStatusEnum,
    ProjectPriorityEnum,
    ProjectFilter
)
from app.models.user import User
from app.models.project import ProjectStatus, ProjectPriority
from app.services.project_service import ProjectService
from app.api.deps import get_current_user, get_project_service


router = APIRouter()

@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new project owned by the current user"
)
async def create_project(
    project_data: ProjectCreate = Body(...),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> ProjectResponse:
   
    project = await project_service.create_project(
        project_data=project_data,
        owner_id=current_user.id
    )
    return project


@router.get(
    "/",
    response_model=List[ProjectResponse],
    summary="List projects",
    description="Get list of projects with optional filters"
)
async def list_projects(
    status: Optional[ProjectStatusEnum] = Query(None, description="Filter by status"),
    priority: Optional[ProjectPriorityEnum] = Query(None, description="Filter by priority"),
    owner_id: Optional[int] = Query(None, description="Filter by owner ID"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> List[ProjectResponse]:
   
    projects = await project_service.get_by_filters(
        status = status,
        priority= priority,
        owner_id=owner_id,
        current_user=current_user,
        skip=skip,
        limit=limit
    )
    
    return projects

@router.get(
    "/my",
    response_model=List[ProjectResponse],
    summary="Get my projects",
    description="Get all projects owned by the current user"
)
async def get_my_projects(
    status: Optional[ProjectStatusEnum] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> List[ProjectResponse]:
    status_filter = ProjectStatus[status.value.upper()] if status else None
    
    projects = await project_service.get_user_projects(
        user_id=current_user.id,
        status=status_filter,
        skip=skip,
        limit=limit
    )
    return projects


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Get a specific project with owner information"
)
async def get_project(
    project_id: int = Path(..., gt=0, description="Project ID"),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> ProjectResponse:
   
    project = await project_service.get_project(project_id, load_owner=True)
    
    if not current_user.is_superuser and project.owner_id != current_user.id:
        from app.utils.exceptions import ForbiddenException
        raise ForbiddenException(
            message="You don't have access to this project",
            details={"project_id": project_id}
        )
    
    return project


