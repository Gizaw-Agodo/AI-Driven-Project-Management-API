from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

from app.schemas.base import BaseSchema, TimestampSchema, IDSchema
from app.schemas.user import UserPublic


# ============== ENUMS ==============

class ProjectStatusEnum(str, Enum):

    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============== INPUT SCHEMAS ==============

class ProjectBase(BaseSchema):

    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    status: ProjectStatusEnum = Field(ProjectStatusEnum.PLANNING)
    priority: ProjectPriorityEnum = Field(ProjectPriorityEnum.MEDIUM)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v and 'start_date' in info.data and info.data['start_date']:
            if v <= info.data['start_date']:
                raise ValueError('end_date must be after start_date')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError('Project name must be at least 3 characters')
        return v.strip()


class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseSchema):

    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[ProjectStatusEnum] = None
    priority: Optional[ProjectPriorityEnum] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectStatusUpdate(BaseSchema):

    status: ProjectStatusEnum = Field(...)
    notes: Optional[str] = Field(None, max_length=500)


# ============== OUTPUT SCHEMAS ==============

class ProjectResponse(ProjectBase, IDSchema, TimestampSchema):

    owner_id: int
    owner: UserPublic  
    

class ProjectWithTasks(ProjectResponse):

    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    blocked_tasks: int = 0
    
    @property
    def completion_percentage(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def is_overdue(self) -> bool:
        if self.end_date and datetime.utcnow() > self.end_date:
            return self.status not in [ProjectStatusEnum.COMPLETED, ProjectStatusEnum.CANCELLED]
        return False


class ProjectListResponse(BaseModel):
    total: int
    projects: list[ProjectResponse]
    
    model_config = ConfigDict(from_attributes=True)


class ProjectFilter(BaseSchema):

    status: Optional[ProjectStatusEnum] = None
    priority: Optional[ProjectPriorityEnum] = None
    owner_id: Optional[int] = None
    search: Optional[str] = Field(None, max_length=255, description="Search in name/description")
    start_date_from: Optional[datetime] = None
    start_date_to: Optional[datetime] = None
    is_overdue: Optional[bool] = None