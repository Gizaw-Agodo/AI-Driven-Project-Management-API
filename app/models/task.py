from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum
from app.db import Base, TimestampMixin

if TYPE_CHECKING : 
    from app.models import Project, User


class TaskStatus(str, Enum): 
    TODO  = 'todo'
    IN_PROGRESS = 'in_progress'
    IN_REVIEW = 'in_review'
    DONE  = 'done'
    BLOCKED  = 'blocked'
    CANCELLED  = 'cancelled'

class TaskPriority(str, Enum): 
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Task(Base , TimestampMixin): 
    __tablename__ = 'tasks'
    id : Mapped[int] = mapped_column(primary_key=True, nullable= False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.TODO, nullable=False, index=True)
    priority : Mapped[TaskPriority] = mapped_column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False, index=True)

    project_id : Mapped[int] =  mapped_column(ForeignKey('projects.id'), nullable=False, index = True)

    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    ai_priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  
    ai_estimated_completion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  
    complexity_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) 
    
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_id])
    creator: Mapped["User"] = relationship( "User", back_populates="created_tasks", foreign_keys=[created_by])
