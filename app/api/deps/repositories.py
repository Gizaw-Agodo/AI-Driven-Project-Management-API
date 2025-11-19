
from fastapi import Depends
from app.api.deps.database import get_db
from app.repositories import TaskRepository, ProjectRepository, UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


def get_user_repo(
    db: AsyncSession = Depends(get_db)
)-> UserRepository: 
    return UserRepository(db)


def get_project_repo(
    db: AsyncSession = Depends(get_db)
)-> ProjectRepository: 
    return ProjectRepository(db)

def get_task_repo(
    db: AsyncSession = Depends(get_db)
)-> TaskRepository: 
    return TaskRepository(db)

