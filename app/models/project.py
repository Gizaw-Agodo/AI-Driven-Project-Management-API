from datetime import datetime, timezone
from sqlite3 import Time
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Enum as SqlEnum, DateTime, ForeignKey
from app.db import Base, TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum


if TYPE_CHECKING : 
    from app.models import User, Task

class ProjectStatus(Enum, str): 
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED  = "completed"
    CANCELLED  = 'cancelled'

class ProjectPriority(Enum, str): 
    LOW = "low"
    MEDIUM =  'medium'
    HIGH  = 'high'
    CRITICAL = 'cretical'

class Project(Base, TimestampMixin): 
    __tablename__ = "projects"
    id:Mapped[int] = mapped_column(primary_key=True, unique=True, index=True)
    name : Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status : Mapped[ProjectStatus] = mapped_column(SqlEnum(ProjectStatus), default= ProjectStatus.PLANNING, nullable=False, index= True)
    priority: Mapped[ProjectPriority] = mapped_column(SqlEnum(ProjectPriority), default= ProjectPriority.MEDIUM, nullable= False, index=True)
    start_date: Mapped(Optional(datetime)) = mapped_column(DateTime, nullable=True)
    end_date: Mapped(Optional(datetime)) = mapped_column(DateTime, nullable=True)
    owner_id : Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, index=True)

    owner : Mapped['User'] = relationship("User", back_populates='owned_projects', foreign_keys=[owner_id])
    tasks : Mapped[List['Task']] = relationship("Task", back_populates = 'project', cascade='all, delete-orphan')

