from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime

from app.models.project import Project, ProjectStatus, ProjectPriority
from app.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """
    Project-specific repository methods.
    
    Advanced queries for project management.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)

    async def get_with_owner(self, project_id) -> Optional[Project]:
        query = select(Project).where(Project.id == project_id).options(
            joinedload(Project.owner)
        )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()
    
    async def get_with_tasks(self, project_id: int) -> Optional[Project]:
        query = select(Project).where(Project.id == project_id).options(
            selectinload(Project.tasks)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_with_full_details(self, project_id: int) -> Optional[Project]:
        
        query = select(Project).where(Project.id == project_id).options(
            joinedload(Project.owner),
            selectinload(Project.tasks)
        )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_by_owner(
        self,
        owner_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        query = select(Project).where(
            Project.owner_id == owner_id
        ).order_by(Project.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list[Project](result.scalars().all())
    
    async def get_by_status(
        self,
        status: ProjectStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        
        query = select(Project).where(
            Project.status == status
        ).order_by(Project.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list[Project](result.scalars().all())
    
    async def get_by_priority(self,priority:ProjectPriority, skip:int = 0 , limit:int = 0) -> List[Project]:
        query = select(Project).where(
            Project.priority == priority
            ).order_by(Project.created_at.desc()
            ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list[Project](result.scalars().all())
    
    async def get_overdue_projects(self) -> List[Project]:
       
        now = datetime.utcnow()
        
        query = select(Project).where(
            and_(
                Project.end_date < now,
                Project.status.not_in([
                    ProjectStatus.COMPLETED,
                    ProjectStatus.CANCELLED
                ])
            )
        ).order_by(Project.end_date)
        
        result = await self.db.execute(query)
        return list[Project](result.scalars().all())
        
    async def get_active_projects_by_owner(self, owner_id: int) -> List[Project]:
        query = select(Project).where(
            and_(
                Project.owner_id == owner_id,
                Project.status == ProjectStatus.ACTIVE
            )
        )
        result = await self.db.execute(query)
        return list[Project](result.scalars().all())
    
    async def count_by_status(self, owner_id: Optional[int] = None) -> Dict[str, int]:
        
        query = select(
            Project.status,
            func.count(Project.id)
        )
        
        if owner_id:
            query = query.where(Project.owner_id == owner_id)
        
        query = query.group_by(Project.status)
        
        result = await self.db.execute(query)
        
        return {status.value: count for status, count in result}


   
    async def get_project_statistics(
        self,
        project_id: int
    ) -> Optional[Dict[str, Any]]:
       
        from app.models.task import Task, TaskStatus
        
         # Query to get task counts
        task_stats = select(
            func.count(Task.id).label('total_tasks'),
            func.count(Task.id).filter(
                Task.status == TaskStatus.DONE
            ).label('completed_tasks'),
            func.count(Task.id).filter(
                Task.status == TaskStatus.IN_PROGRESS
            ).label('in_progress_tasks'),
            func.count(Task.id).filter(
                Task.status == TaskStatus.BLOCKED
            ).label('blocked_tasks'),
            func.avg(Task.estimated_hours).label('avg_estimated_hours'),
            func.sum(Task.actual_hours).label('total_actual_hours')
        ).where(Task.project_id == project_id)
        
        result = await self.db.execute(task_stats)
        stats = result.one_or_none()
        
        if not stats:
            return None
        
        return {
            'total_tasks': stats.total_tasks or 0,
            'completed_tasks': stats.completed_tasks or 0,
            'in_progress_tasks': stats.in_progress_tasks or 0,
            'blocked_tasks': stats.blocked_tasks or 0,
            'avg_estimated_hours': float(stats.avg_estimated_hours or 0),
            'total_actual_hours': float(stats.total_actual_hours or 0),
            'completion_rate': (
                (stats.completed_tasks / stats.total_tasks * 100)
                if stats.total_tasks > 0 else 0
            )
        }