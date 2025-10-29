from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
import re

from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


# ============== INPUT SCHEMAS (Request) ==============

class UserBase(BaseSchema):
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Username (alphanumeric, dash, underscore only)"
    )
    full_name: Optional[str] = Field(None, max_length=255)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if v.lower() in ['admin', 'root', 'system', 'api']:
            raise ValueError('Username is reserved')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must be alphanumeric with dash/underscore')
        return v
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate full name if provided"""
        if v and len(v.strip()) == 0:
            return None
        return v


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (min 8 chars, must include uppercase, lowercase, digit)"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:

        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    


class UserUpdate(BaseSchema):

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    


class UserPasswordUpdate(BaseSchema):

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


# ============== OUTPUT SCHEMAS (Response) ==============

class UserResponse(UserBase, IDSchema, TimestampSchema):

    is_active: bool
    is_superuser: bool
    


class UserPublic(IDSchema):

    username: str
    full_name: Optional[str]
    


class UserWithStats(UserResponse):

    total_projects: int = Field(0, description="Number of owned projects")
    total_tasks: int = Field(0, description="Number of assigned tasks")
    completed_tasks: int = Field(0, description="Number of completed tasks")
    
    @property
    def completion_rate(self) -> float:
        """Calculate task completion rate"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100


class UserListResponse(BaseModel):

    total: int
    users: list[UserResponse]
    
    model_config = ConfigDict(from_attributes=True)