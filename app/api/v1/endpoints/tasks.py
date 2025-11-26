from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, Path, Body

from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatusUpdate,
    TaskAssignmentUpdate,
    TaskStatusEnum,
    TaskPriorityEnum,
    TaskFilter,
    TaskStatistics
)
from app.models.user import User
from app.models.task import TaskStatus, TaskPriority
from app.services.task_service import TaskService
from app.api.deps import get_current_user, get_task_service


router = APIRouter()


# ==================== CREATE OPERATIONS ====================

@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Create a new task in a project"
)
async def create_task(
    task_data: TaskCreate = Body(...),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    
    task = await task_service.create_task(
        task_data=task_data,
        creator_id=current_user.id
    )
    return task


# ==================== READ OPERATIONS ====================

@router.get(
    "/",
    response_model=List[TaskResponse],
    summary="List tasks",
    description="Get list of tasks with filters"
)
async def list_tasks(
    # 🎓 ADVANCED: Complex Filtering System
    project_id: Optional[int] = Query(None, description="Filter by project"),
    assignee_id: Optional[int] = Query(None, description="Filter by assignee"),
    status: Optional[TaskStatusEnum] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriorityEnum] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    has_assignee: Optional[bool] = Query(None, description="Filter by assignment status"),
    complexity_min: Optional[int] = Query(None, ge=1, le=10, description="Min complexity"),
    complexity_max: Optional[int] = Query(None, ge=1, le=10, description="Max complexity"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> List[TaskResponse]:
    
    # Build filters
    filters = {}
    
    if project_id:
        filters['project_id'] = project_id
    if assignee_id:
        filters['assignee_id'] = assignee_id
    if status:
        filters['status'] = TaskStatus[status.value.upper()]
    if priority:
        filters['priority'] = TaskPriority[priority.value.upper()]
    
    # Handle search
    if search:
        tasks = await task_service.task_repo.search_tasks(
            search_term=search,
            project_id=project_id,
            assignee_id=assignee_id,
            skip=skip,
            limit=limit
        )
    else:
        # Get with filters
        tasks = await task_service.task_repo.get_by_filters(
            filters=filters,
            skip=skip,
            limit=limit,
            relationships=["assignee", "creator", "project"]
        )
    
    # Apply additional filters
    if has_assignee is not None:
        tasks = [t for t in tasks if (t.assignee_id is not None) == has_assignee]
    
    if complexity_min is not None:
        tasks = [t for t in tasks if t.complexity_score and t.complexity_score >= complexity_min]
    
    if complexity_max is not None:
        tasks = [t for t in tasks if t.complexity_score and t.complexity_score <= complexity_max]
    
    return tasks


@router.get(
    "/my",
    response_model=List[TaskResponse],
    summary="Get my assigned tasks",
    description="Get all tasks assigned to current user"
)
async def get_my_tasks(
    status: Optional[TaskStatusEnum] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> List[TaskResponse]:
    
    status_filter = TaskStatus[status.value.upper()] if status else None
    
    tasks = await task_service.get_user_tasks(
        user_id=current_user.id,
        status=status_filter,
        skip=skip,
        limit=limit
    )
    return tasks


@router.get(
    "/my/overdue",
    response_model=List[TaskResponse],
    summary="Get my overdue tasks",
    description="Get current user's overdue tasks"
)
async def get_my_overdue_tasks(
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> List[TaskResponse]:
    
    tasks = await task_service.get_overdue_tasks(assignee_id=current_user.id)
    return tasks


@router.get(
    "/high-priority",
    response_model=List[TaskResponse],
    summary="Get high priority tasks",
    description="Get high/critical priority tasks"
)
async def get_high_priority_tasks(
    project_id: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> List[TaskResponse]:
   
    tasks = await task_service.get_high_priority_tasks(
        project_id=project_id,
        limit=limit
    )
    
    # Filter by authorization
    if not current_user.is_superuser:
        # Show only if user is owner, creator, or assignee
        tasks = [
            t for t in tasks
            if (t.project.owner_id == current_user.id or
                t.created_by == current_user.id or
                t.assignee_id == current_user.id)
        ]
    
    return tasks


@router.get(
    "/statistics",
    response_model=TaskStatistics,
    summary="Get task statistics",
    description="Get aggregated task statistics"
)
async def get_task_statistics(
    project_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> TaskStatistics:
   
    # Authorization
    if assignee_id and assignee_id != current_user.id and not current_user.is_superuser:
        from app.utils.exceptions import ForbiddenException
        raise ForbiddenException("Cannot view other users' statistics")
    
    stats = await task_service.get_task_statistics(
        project_id=project_id,
        assignee_id=assignee_id
    )
    return stats


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task by ID",
    description="Get a specific task with all relations"
)
async def get_task(
    task_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    
    task = await task_service.get_task(task_id, load_relations=True)
    
    # Check authorization
    is_authorized = (
        current_user.is_superuser or
        task.project.owner_id == current_user.id or
        task.created_by == current_user.id or
        task.assignee_id == current_user.id
    )
    
    if not is_authorized:
        from app.utils.exceptions import ForbiddenException
        raise ForbiddenException("Access denied")
    
    return task


# ==================== NESTED RESOURCE: Project Tasks ====================

@router.get(
    "/projects/{project_id}/tasks",
    response_model=List[TaskResponse],
    summary="Get project tasks",
    description="Get all tasks for a specific project"
)
async def get_project_tasks(
    project_id: int = Path(..., gt=0, description="Project ID"),
    status: Optional[TaskStatusEnum] = Query(None),
    assignee_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> List[TaskResponse]:
   
    # Verify project access
    from app.services.project_service import ProjectService
    project_service = ProjectService(task_service.db)
    project = await project_service.get_project(project_id)
    
    if not current_user.is_superuser and project.owner_id != current_user.id:
        from app.utils.exceptions import ForbiddenException
        raise ForbiddenException("Access denied to this project")
    
    status_filter = TaskStatus[status.value.upper()] if status else None
    
    tasks = await task_service.get_project_tasks(
        project_id=project_id,
        status=status_filter,
        assignee_id=assignee_id,
        skip=skip,
        limit=limit
    )
    return tasks


# ==================== UPDATE OPERATIONS ====================

@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    description="Update task information"
)
async def update_task(
    task_id: int = Path(..., gt=0),
    task_data: TaskUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    
    updated_task = await task_service.update_task(
        task_id=task_id,
        task_data=task_data,
        current_user_id=current_user.id
    )
    return updated_task


@router.put(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="Update task status",
    description="Update task status with state machine validation"
)
async def update_task_status(
    task_id: int = Path(..., gt=0),
    status_data: TaskStatusUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
   
    updated_task = await task_service.update_task_status(
        task_id=task_id,
        status_data=status_data,
        current_user_id=current_user.id
    )
    return updated_task


@router.put(
    "/{task_id}/assign",
    response_model=TaskResponse,
    summary="Assign task",
    description="Assign or reassign task to a user"
)
async def assign_task(
    task_id: int = Path(..., gt=0),
    assignment_data: TaskAssignmentUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    
    updated_task = await task_service.assign_task(
        task_id=task_id,
        assignment_data=assignment_data,
        current_user_id=current_user.id
    )
    return updated_task


@router.post(
    "/bulk/status",
    summary="Bulk update task status",
    description="Update status for multiple tasks at once"
)
async def bulk_update_task_status(
    task_ids: List[int] = Body(..., description="List of task IDs"),
    new_status: TaskStatusEnum = Body(..., description="New status"),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
   
    status_enum = TaskStatus[new_status.value.upper()]
    
    result = await task_service.bulk_update_status(
        task_ids=task_ids,
        new_status=status_enum,
        current_user_id=current_user.id
    )
    
    return result


# ==================== DELETE OPERATIONS ====================

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Delete a task (creator or project owner only)"
)
async def delete_task(
    task_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
   
    await task_service.delete_task(
        task_id=task_id,
        current_user_id=current_user.id
    )