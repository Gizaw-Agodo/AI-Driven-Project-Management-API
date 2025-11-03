import datetime
from typing import List
from typing_extensions import Optional
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import joinedload
from app.models.task import Task, TaskPriority, TaskStatus
from app.repositories.base_repository import BaseRepository
from app.models import Project, Task

class TaskRePository(BaseRepository[Task]):
    def __init__(self, db):
        super().__init__(Task, db)
    
    async def get_with_relations(self, task_id : int):
        query = select(Task).where(Task.id == task_id).options(
            joinedload(Task.project).joinedload(Project.owner),
            joinedload(Task.assignee),
            joinedload(Task.creator)
        )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()
    
    async def get_by_project(self, project_id : int , skip : int = 0, limit : int = 100):
        query = select(Task).where(Task.project_id == project_id).where(
            joinedload(Task.assignee),
            joinedload(Task.creator)
        ).order_by(Task.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.unique().scalars().all()

    async def get_by_assignee(self, assignee_id : int,  status : Optional[TaskStatus], skip : int = 0 , limit : int = 100):
        conditions = [Task.assignee_id == assignee_id]
        
        if status:
            conditions.append(Task.status == status)
        
        query = select(Task).where(
            and_(*conditions)
        ).options(
            joinedload(Task.project)
        ).order_by(Task.due_date.nullsfirst(), Task.priority).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list[Task](result.unique().scalars().all())
    
    async def get_unassigned_tasks(self, skip:int = 0 , limit : int = 0):
        query = select(Task).where(Task.assignee_id.is_(None)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()


    async def get_overdue_tasks(self):
        query = select(Task).where(
            and_(
                Task.due_date < datetime.utcnow(),
                Task.status.not_in(TaskStatus.DONE, TaskStatus.CANCELLED)
            )
        ).options(
            joinedload(Task.assignee),
            joinedload(Task.project)
        ).order_by(Task.due_date)

        result = await self.db.execute(query)
        return list[Task](result.unique().scalars().all())


    async def get_tasks_by_complexity(
        self,
        min_complexity: int,
        max_complexity: int,
        project_id: Optional[int] = None
    ) -> List[Task]:
        conditions = [
            Task.complexity_score >= min_complexity,
            Task.complexity_score <= max_complexity
        ]
        
        if project_id:
            conditions.append(Task.project_id == project_id)
        
        query = select(Task).where(
            and_(*conditions)
        ).order_by(Task.complexity_score.desc())
        
        result = await self.db.execute(query)
        return list[Task](result.scalars().all())
    
    async def get_task_statistics(
        self, 
        project_id : Optional[int] = None, 
        assignee_id : Optional[int] = None
    ):
        conditions = []
        if project_id:
            conditions.append(Task.project_id == project_id)
        if assignee_id: 
            conditions.append(Task.assignee_id == assignee_id)
        
        query = select(
            func.count(Task.id).label("total_tasks"),
            func.count(case((Task.status == TaskStatus.TODO, 1))).label('todo'),
            func.count(case((Task.status == TaskStatus.IN_PROGRESS, 1))).label('in_progress'),
            func.count(case((Task.status == TaskStatus.IN_REVIEW, 1))).label('in_review'),
            func.count(case((Task.status == TaskStatus.DONE, 1))).label('done'),
            func.count(case((Task.status == TaskStatus.BLOCKED, 1))).label('blocked'),
            func.count(case((Task.priority == TaskPriority.CRITICAL, 1))).label('critical'),
            func.count(case((Task.priority == TaskPriority.HIGH, 1))).label('high'),
            func.count(case((Task.priority == TaskPriority.MEDIUM, 1))).label('medium'),
            func.count(case((Task.priority == TaskPriority.LOW, 1))).label('low'),
            func.avg(Task.estimated_hours).label('avg_estimated'),
            func.avg(Task.actual_hours).label('avg_actual'),
            func.avg(Task.complexity_score).label('avg_complexity'),
            func.count(case((Task.due_date < datetime.utcnow(), 1))).label('overdue')
        )
        if conditions:
            query = query.where(and_(*conditions))
        

        result = await self.db.execute(query)
        stats = result.one()
        
        return {
            'total_tasks': stats.total_tasks,
            'by_status': {
                'todo': stats.todo,
                'in_progress': stats.in_progress,
                'in_review': stats.in_review,
                'done': stats.done,
                'blocked': stats.blocked
            },
            'by_priority': {
                'critical': stats.critical,
                'high': stats.high,
                'medium': stats.medium,
                'low': stats.low
            },
            'avg_estimated_hours': float(stats.avg_estimated or 0),
            'avg_actual_hours': float(stats.avg_actual or 0),
            'avg_complexity': float(stats.avg_complexity or 0),
            'overdue_count': stats.overdue,
            'completion_rate': (
                (stats.done / stats.total_tasks * 100)
                if stats.total_tasks > 0 else 0
            )
        }
    
    async def assign_task(
        self,
        task_id: int,
        assignee_id: Optional[int]
    ) -> Optional[Task]:

        return await self.update(task_id, {'assignee_id': assignee_id})
    
    async def complete_task(self, task_id: int) -> Optional[Task]:
        return await self.update(task_id, {
            'status': TaskStatus.DONE,
            'completed_at': datetime.utcnow()
        })
    
    async def get_high_priority_tasks(
        self,
        project_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Task]:
        pass