from dataclasses import field
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema
import re


# ============== INPUT SCHEMAS (Request) ==============

class UserBase(BaseSchema):
    email: EmailStr = Field(...)
    username: str = Field(..., min_length= 3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    full_name: Optional[str] = Field(None, max_length=255)
    
    @field_validator('username')
    def validate_full_name(v:str):
        if v.lower() in ['admin', 'root', 'system','api']:
            raise ValueError('Username is reserved')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must be alphanumeric with dash/underscore')
        return v

class UserCreate(UserBase): 
    password : str = Field(..., min_length=8, max_length=100)
    
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
    

# ============== OUTPUT SCHEMAS (Response) ==============

class UserResponse(UserBase, IDSchema, TimestampSchema): 
    is_active: bool
    is_superuser:bool

class UserWithStatus(UserResponse): 
    total_projects : int = Field(0, description='Number of owned projects')
    total_tasks : int = Field(0, description='Number of assigned tasks')
    completed_tasks: int = Field(0, description="Number of completed tasks")

    @property
    def completion_rate(self) -> float:
        if self.total_tasks == 0 : 
            return 0.0
        return (self.completed_tasks/self.total_tasks)

class UserListResponse(BaseSchema): 
    total : int 
    users : list(UserResponse)
