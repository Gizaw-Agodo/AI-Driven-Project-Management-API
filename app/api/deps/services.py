from fastapi import Depends
from app.repositories import ProjectRepository, TaskRepository, UserRepository
from app.services import TaskService, UserService, ProjectService

async def get_user_service(
    user_repo: UserRepository = Depends(lambda: __import__('app.api.deps').api.deps.get_user_repo())
) -> UserService:
    return UserService(user_repo)

async def get_project_service(
    user_repo: UserRepository = Depends(lambda: __import__('app.api.deps').api.deps.get_user_repo()),
    project_repo: ProjectRepository = Depends(lambda: __import__('app.api.deps').api.deps.get_project_repo())
) -> ProjectService:
    return ProjectService(user_repo, project_repo)

async def get_task_service(
    task_repo: TaskRepository = Depends(lambda: __import__('app.api.deps').api.deps.get_task_repo()),
    user_repo: UserRepository = Depends(lambda: __import__('app.api.deps').api.deps.get_user_repo()),
    project_repo: ProjectRepository = Depends(lambda: __import__('app.api.deps').api.deps.get_project_repo())
) -> TaskService:
    return TaskService(task_repo, project_repo, user_repo)
