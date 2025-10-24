from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base, TimestampMixin
from typing import List, TYPE_CHECKING

if TYPE_CHECKING: 
    from app.models import Project, Task

class User(Base , TimestampMixin): 
    __tablename__ = 'users'
    id : Mapped[int] = mapped_column(primary_key=True,index = True )
    email : Mapped[str] = mapped_column(String(255), unique= True, nullable= False, index = True)
    username : Mapped[str] = mapped_column(String(100), unique=True, nullable= False, index=True)
    full_name : Mapped[str] = mapped_column(String(200), nullable= True)
    hashed_password : Mapped[str] = mapped_column(String(255), nullable=False)
    is_active : Mapped[bool] = mapped_column(Boolean, default=True, nullable= False)
    is_superuser : Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
  
    owned_projects : Mapped[List['Project']] = relationship(
        "Project", back_populates='owner', foreign_keys='Project.owner_id', cascade="all, delete-orphan"
    )

    assigned_tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="assignee", foreign_keys="Task.assignee_id"
    )
    
    created_tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="creator", foreign_keys="Task.created_by"
    )