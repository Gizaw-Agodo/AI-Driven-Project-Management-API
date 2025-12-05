from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

from app.schemas.base import BaseSchema, TimestampSchema, IDSchema
from app.schemas.user import UserPublic
from app.schemas.project import ProjectResponse


# ============== ENUMS ==============

class TaskStatusEnum(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============== INPUT SCHEMAS ==============

class TaskBase(BaseSchema):
   
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    status: TaskStatusEnum = Field(TaskStatusEnum.TODO)
    priority: TaskPriorityEnum = Field(TaskPriorityEnum.MEDIUM)
    
    # Time estimation
    estimated_hours: Optional[float] = Field(None, ge=0, le=1000)
    actual_hours: Optional[float] = Field(None, ge=0, le=1000)
    
    ai_priority_score: Optional[float] = Field(None, ge=0, le=10)
    complexity_score: Optional[int] = Field(None, ge=1, le=10)
    
    # Dates
    due_date: Optional[datetime] = None
    
    @field_validator('actual_hours')
    @classmethod
    def validate_actual_hours(cls, v: Optional[float], info) -> Optional[float]:
        if v and 'estimated_hours' in info.data and info.data['estimated_hours']:
            if v > info.data['estimated_hours'] * 3:
                # Warning: actual is 3x more than estimated
                # In production, you might log this or trigger notifications
                pass
        return v


class TaskCreate(TaskBase):
    project_id: int = Field(..., gt=0)
    assignee_id: Optional[int] = Field(None, gt=0)
    


class TaskUpdate(BaseSchema):
  
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    status: Optional[TaskStatusEnum] = None
    priority: Optional[TaskPriorityEnum] = None
    assignee_id: Optional[int] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    due_date: Optional[datetime] = None
    
    @field_validator('status')
    @classmethod
    def validate_status_transition(cls, v: Optional[TaskStatusEnum], info) -> Optional[TaskStatusEnum]:
        """
        Advanced: Status transition validation.
        
        This is a simplified version. In production, you'd check:
        - Current status from database
        - Valid transitions (e.g., can't go from DONE to TODO)
        - User permissions for certain transitions
        """
        # Example: Business rule - cancelled tasks can't be reopened
        # You'd implement this in service layer with current status check
        return v


class TaskStatusUpdate(BaseSchema):
    """Quick status update with notes"""
    status: TaskStatusEnum
    notes: Optional[str] = Field(None, max_length=1000)
    actual_hours: Optional[float] = Field(None, ge=0)


class TaskAssignmentUpdate(BaseSchema):
    """Separate schema for task assignment"""
    assignee_id: Optional[int] = None


# ============== OUTPUT SCHEMAS ==============

class TaskResponse(TaskBase, IDSchema, TimestampSchema):
    """
    Complete task response.
    
    Advanced: Includes nested relations (project, assignee, creator)
    """
    project_id: int
    assignee_id: Optional[int]
    created_by: int
    completed_at: Optional[datetime]
    ai_estimated_completion: Optional[datetime]
    
    # Nested objects (loaded via selectinload/joinedload)
    assignee: Optional[UserPublic] = None
    creator: UserPublic
    



class TaskWithProject(TaskResponse):
    project: ProjectResponse


class TaskListResponse(BaseModel):
    """Paginated task list"""
    total: int
    tasks: list[TaskResponse]
    
    model_config = ConfigDict(from_attributes=True)


class TaskFilter(BaseSchema):
    
    status: Optional[TaskStatusEnum] = None
    priority: Optional[TaskPriorityEnum] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    created_by: Optional[int] = None
    search: Optional[str] = Field(None, description="Search in title/description")
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None
    is_overdue: Optional[bool] = None
    has_assignee: Optional[bool] = None
    complexity_min: Optional[int] = Field(None, ge=1, le=10)
    complexity_max: Optional[int] = Field(None, ge=1, le=10)


class TaskStatistics(BaseModel):
    total_tasks: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    average_completion_time: Optional[float]  # hours
    overdue_count: int
    blocked_count: int
    