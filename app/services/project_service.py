from typing import Optional, List

from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectStatusUpdate
from app.models.project import Project, ProjectStatus
from app.utils.exceptions import ( NotFoundException,ValidationException,ForbiddenException,BusinessLogicException)

class ProjectService:
    def __init__(self,user_repo:UserRepository, project_repo : ProjectRepository):
        self.project_repo = project_repo
        self.user_repo = user_repo
    
    async def create_project(self, project_data : ProjectCreate, owner_id:int):
        #verify owner 
        owner = await self.user_repo.get_by_id(owner_id)
        if not owner :
            raise NotFoundException("Owner not found")
        if not owner.is_active:
            raise ValidationException("Owner is not active")
        
        project_dict = project_data.model_dump()
        project_dict["owner_id"] = owner_id

        project = await self.project_repo.create(project_dict)
        project = await self.project_repo.get_with_owner(project.id)

        return project
    async def get_project(
        self,
        project_id: int,
        load_owner: bool = True,
        load_tasks: bool = False
    ) -> Project:
        if load_tasks:
            project = await self.project_repo.get_with_tasks(project_id)
        elif load_owner:
            project = await self.project_repo.get_with_owner(project_id)
        else:
            project = await self.project_repo.get_by_id(project_id)
        
        if not project:
            raise NotFoundException( message=f"Project with ID {project_id} not found")
        
        return project
    
    async def update_project(
        self,
        project_id: int,
        project_data: ProjectUpdate,
        current_user_id: int
    ) -> Project:
        
        project = await self.get_project(project_id)
        
        # Authorization: Check if user is owner
        if project.owner_id != current_user_id:
            raise ForbiddenException( message="You don't have permission to update this project")
        
        # Validate date changes
        update_dict = project_data.model_dump(exclude_unset=True)
        
        if "status" in update_dict:
            del update_dict["status"]

        await self.project_repo.update(project_id,update_dict)
        
        # Reload with owner
        return await self.project_repo.get_with_owner(project_id)


    async def update_project_status(
        self,
        project_id: int,
        status_data: ProjectStatusUpdate,
        current_user_id: int
    ) -> Project:
        
        project = await self.get_project(project_id, load_tasks=True)
        
        # Authorization check
        if project.owner_id != current_user_id:
            raise ForbiddenException(message="Only project owner can change status")
        
        new_status = status_data.status
        current_status = project.status
        
        # Business Rule: Validate status transitions
        if current_status == ProjectStatus.PLANNING and new_status == ProjectStatus.ACTIVE:
            if not project.start_date:
                raise BusinessLogicException( message="Cannot activate project without start date")

        if current_status == ProjectStatus.ACTIVE and new_status == ProjectStatus.COMPLETED:
            # Check if all tasks are done
            incomplete_tasks = sum(1 for task in project.tasks if task.status.value not in ["done", "cancelled"])
            
            if incomplete_tasks > 0:
                raise BusinessLogicException( message=f"Cannot complete project with {incomplete_tasks} incomplete tasks")
        
        if new_status == ProjectStatus.ON_HOLD and not status_data.notes:
            raise ValidationException( message="Reason required when putting project on hold")
        
         # Update status
        await self.project_repo.update_status( project_id,new_status)
        
        return await self.project_repo.get_with_owner(project_id)

    async def delete_project(
        self,
        project_id: int,
        current_user_id: int,
        force: bool = False
    ) -> bool:

        project = await self.get_project(project_id, load_tasks=True)
        
        # Authorization
        if project.owner_id != current_user_id:
            raise ForbiddenException( message="Only project owner can delete project")
        
        # Business Rule: Cannot delete project with tasks unless forced
        if project.tasks and not force:
            raise BusinessLogicException(message=f"Cannot delete project with {len(project.tasks)} tasks",)
        
        # Delete project (CASCADE will delete tasks)
        success = await self.project_repo.delete(project_id)
        
        return success

    async def get_user_projects(
        self,
        user_id: int,
        status: Optional[ProjectStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Get all projects owned by a user."""
        projects = await self.project_repo.get_by_owner(
            owner_id=user_id,
            skip=skip,
            limit=limit
        )
        
        if status:
            projects = [p for p in projects if p.status == status]
        
        return projects
