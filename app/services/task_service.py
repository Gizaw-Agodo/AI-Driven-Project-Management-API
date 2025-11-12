from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.repositories.task_repository import TaskRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskAssignmentUpdate
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import ProjectStatus
from app.utils.exceptions import (NotFoundException,ValidationException,ForbiddenException,BusinessLogicException)


class TaskService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_repo = TaskRepository(db)
        self.project_repo = ProjectRepository(db)
        self.user_repo = UserRepository(db)

    async def create_task(
        self,
        task_data: TaskCreate,
        creator_id: int
    ) -> Task:
                
        # Step 1: Verify project exists and is active
        project = await self.project_repo.get_by_id(task_data.project_id)
        if not project:
            raise NotFoundException( message=f"Project with ID {task_data.project_id} not found")
        
        # 🆕 Business Rule: Cannot create tasks in cancelled projects
        if project.status == ProjectStatus.CANCELLED:
            raise BusinessLogicException(message="Cannot create tasks in cancelled projects")
        
        # 🆕 Business Rule: Cannot create tasks in completed projects
        if project.status == ProjectStatus.COMPLETED:
            raise BusinessLogicException(message="Cannot create tasks in completed projects")
        
        # Step 2: Verify creator exists and has access
        creator = await self.user_repo.get_by_id(creator_id)
        if not creator:
            raise NotFoundException(message=f"Creator with ID {creator_id} not found")
        
        if not creator.is_active:
            raise ValidationException(message="Inactive users cannot create tasks")
        
        if project.owner_id != creator_id:
            raise ForbiddenException(
                message="Only project owner can create tasks")
        
        # Step 3: Verify assignee exists (if provided)
        if task_data.assignee_id:
            assignee = await self.user_repo.get_by_id(task_data.assignee_id)
            if not assignee:
                raise NotFoundException(
                    message=f"Assignee with ID {task_data.assignee_id} not found"
                )
            
            if not assignee.is_active:
                raise ValidationException(
                    message="Cannot assign tasks to inactive users"                )
        
        # 🆕 Business Rule: Validate due date
        if task_data.due_date:
            # Due date should be within project timeframe
            if project.end_date and task_data.due_date > project.end_date:
                raise ValidationException(
                    message="Task due date cannot exceed project end date",)

        task_dict = task_data.model_dump()
        task_dict["created_by"] = creator_id
        
        # 🆕 AI INTEGRATION POINT: Calculate complexity score
        if not task_dict.get("complexity_score"):
            task_dict["complexity_score"] = await self._calculate_complexity_score(
                title=task_dict["title"],
                description=task_dict.get("description"),
                estimated_hours=task_dict.get("estimated_hours")
            )
        
        # 🆕 AI INTEGRATION POINT: Calculate AI priority score
        if not task_dict.get("ai_priority_score"):
            task_dict["ai_priority_score"] = await self._calculate_ai_priority(
                priority=task_dict["priority"],
                due_date=task_dict.get("due_date"),
                complexity=task_dict.get("complexity_score")
            )
        
        # 🆕 AI INTEGRATION POINT: Estimate completion date
        task_dict["ai_estimated_completion"] = await self._estimate_completion_date(
            estimated_hours=task_dict.get("estimated_hours"),
            complexity=task_dict.get("complexity_score"),
            assignee_id=task_dict.get("assignee_id")
        )
        
        # Step 5: Create task
        task = await self.task_repo.create(task_dict)
        
        # Step 6: Load with relations for response
        task = await self.task_repo.get_with_relations(task.id)
        
        # 🆕 TODO: Trigger notification to assignee
        # await self.notification_service.notify_task_assigned(task)
        
        return task

    async def _calculate_complexity_score(
        self,
        title: str,
        description: Optional[str],
        estimated_hours: Optional[float]
    ) -> int:
       
        score = 5  # Default medium complexity
        
        # Adjust based on estimated hours
        if estimated_hours:
            if estimated_hours <= 2:
                score = 2
            elif estimated_hours <= 8:
                score = 4
            elif estimated_hours <= 24:
                score = 6
            elif estimated_hours <= 80:
                score = 8
            else:
                score = 10
        
        # Adjust based on description
        if description:
            # Long descriptions might indicate complexity
            if len(description) > 500:
                score = min(10, score + 1)
            
            # Technical keywords
            technical_keywords = [
                'database', 'api', 'migration', 'integration',
                'architecture', 'security', 'performance', 'algorithm'
            ]
            
            description_lower = description.lower()
            keyword_count = sum(
                1 for keyword in technical_keywords
                if keyword in description_lower
            )
            
            score = min(10, score + keyword_count)
        
        # TODO: Replace with actual AI/ML model
        # score = await self.ai_service.predict_complexity(title, description)
        
        return max(1, min(10, score))

    async def _calculate_ai_priority(
        self,
        priority: TaskPriority,
        due_date: Optional[datetime],
        complexity: Optional[int]
    ) -> float:
        """
        🆕 AI INTEGRATION: Calculate AI-driven priority score.
        
        Combines:
        - User-set priority
        - Due date urgency
        - Complexity
        - Project context (future)
        
        Returns:
            Priority score (0-10, float)
        """
        # Base score from priority
        priority_scores = {
            TaskPriority.LOW: 2.0,
            TaskPriority.MEDIUM: 5.0,
            TaskPriority.HIGH: 7.5,
            TaskPriority.CRITICAL: 9.5
        }
        
        score = priority_scores.get(priority, 5.0)
        
        # Adjust for due date urgency
        if due_date:
            days_until_due = (due_date - datetime.utcnow()).days
            
            if days_until_due < 0:
                # Overdue - increase priority
                score = min(10.0, score + 2.0)
            elif days_until_due <= 1:
                score = min(10.0, score + 1.5)
            elif days_until_due <= 3:
                score = min(10.0, score + 1.0)
            elif days_until_due <= 7:
                score = min(10.0, score + 0.5)
        
        # Adjust for complexity
        if complexity:
            # High complexity might need earlier attention
            if complexity >= 8:
                score = min(10.0, score + 0.5)
        
        # TODO: Use ML model for better prediction
        # score = await self.ai_service.calculate_priority(...)
        
        return round(score, 2)

    async def _estimate_completion_date(
        self,
        estimated_hours: Optional[float],
        complexity: Optional[int],
        assignee_id: Optional[int]
    ) -> Optional[datetime]:
        """
        🆕 AI INTEGRATION: Estimate task completion date.
        
        Factors:
        - Estimated hours
        - Complexity
        - Assignee's current workload (future)
        - Historical completion rates (future)
        
        Returns:
            Estimated completion datetime or None
        """
        if not estimated_hours:
            return None
        
        # Base calculation: working hours per day
        working_hours_per_day = 6  # Assuming 6 productive hours/day
        
        # Adjust for complexity
        if complexity:
            if complexity >= 8:
                # Complex tasks take longer
                estimated_hours *= 1.3
            elif complexity >= 6:
                estimated_hours *= 1.15
        
        # Calculate days needed
        days_needed = estimated_hours / working_hours_per_day
        
        # TODO: Check assignee's workload
        # if assignee_id:
        #     workload = await self._get_assignee_workload(assignee_id)
        #     days_needed += workload.buffer_days
        
        # Add buffer (20% for uncertainties)
        days_needed *= 1.2
        
        # Calculate completion date (skip weekends in production)
        completion_date = datetime.utcnow() + timedelta(days=days_needed)
        
        return completion_date

    async def get_task(
        self,
        task_id: int,
        load_relations: bool = True
    ) -> Task:
        """Get task by ID."""
        if load_relations:
            task = await self.task_repo.get_with_relations(task_id)
        else:
            task = await self.task_repo.get_by_id(task_id)
        
        if not task:
            raise NotFoundException(
                message=f"Task with ID {task_id} not found",
                details={"task_id": task_id}
            )
        
        return task

    async def update_task(
        self,
        task_id: int,
        task_data: TaskUpdate,
        current_user_id: int
    ) -> Task:
        """
        Update task.
        
        🆕 ADVANCED AUTHORIZATION:
        Who can update tasks?
        1. Task creator
        2. Project owner
        3. Task assignee (limited fields)
        4. Superuser (future)
        
        Different users have different permissions:
        - Creator/Owner: Can update everything
        - Assignee: Can only update status, actual_hours
        """
        task = await self.get_task(task_id, load_relations=True)
        
        # 🆕 ADVANCED: Complex authorization logic
        is_creator = task.created_by == current_user_id
        is_assignee = task.assignee_id == current_user_id
        is_project_owner = task.project.owner_id == current_user_id
        
        # Check if user has any permission
        if not (is_creator or is_assignee or is_project_owner):
            raise ForbiddenException(
                message="You don't have permission to update this task",
                details={
                    "task_id": task_id,
                    "current_user_id": current_user_id
                }
            )
        
        # 🆕 ADVANCED: Field-level permissions
        update_dict = task_data.model_dump(exclude_unset=True)
        
        # If user is only assignee (not creator/owner), restrict fields
        if is_assignee and not (is_creator or is_project_owner):
            allowed_fields = {"status", "actual_hours", "description"}
            forbidden_fields = set(update_dict.keys()) - allowed_fields
            
            if forbidden_fields:
                raise ForbiddenException(
                    message="Assignees can only update status, actual_hours, and description",
                    details={"forbidden_fields": list(forbidden_fields)}
                )
        
        # Validate assignee change
        if "assignee_id" in update_dict:
            new_assignee_id = update_dict["assignee_id"]
            
            if new_assignee_id:
                assignee = await self.user_repo.get_by_id(new_assignee_id)
                if not assignee or not assignee.is_active:
                    raise ValidationException(
                        message="Invalid assignee",
                        details={"assignee_id": new_assignee_id}
                    )
        
        # 🆕 Business Rule: Validate actual_hours
        if "actual_hours" in update_dict:
            actual_hours = update_dict["actual_hours"]
            
            if actual_hours and actual_hours < 0:
                raise ValidationException(
                    message="Actual hours cannot be negative"
                )
            
            # Warning if actual hours significantly exceed estimate
            if (actual_hours and task.estimated_hours and 
                actual_hours > task.estimated_hours * 2):
                # TODO: Log warning or notify project owner
                pass
        
        # Update task
        updated_task = await self.task_repo.update(task_id, update_dict)
        
        # 🆕 Recalculate AI fields if significant changes
        if any(field in update_dict for field in ["title", "description", "estimated_hours"]):
            # Recalculate complexity
            new_complexity = await self._calculate_complexity_score(
                title=updated_task.title,
                description=updated_task.description,
                estimated_hours=updated_task.estimated_hours
            )
            await self.task_repo.update(task_id, {"complexity_score": new_complexity})
        
        return await self.task_repo.get_with_relations(task_id)

    async def update_task_status(
        self,
        task_id: int,
        status_data: TaskStatusUpdate,
        current_user_id: int
    ) -> Task:
        """
        Update task status with validation.
        
        🆕 STATE MACHINE PATTERN:
        Valid status transitions:
        - TODO -> IN_PROGRESS
        - IN_PROGRESS -> IN_REVIEW
        - IN_PROGRESS -> BLOCKED
        - IN_REVIEW -> DONE
        - IN_REVIEW -> IN_PROGRESS (needs revision)
        - BLOCKED -> IN_PROGRESS (unblocked)
        - Any -> CANCELLED
        
        Business Rules:
        - Completing task requires actual_hours
        - Blocking task requires notes
        - Status change triggers notifications
        """
        task = await self.get_task(task_id, load_relations=True)
        
        # Authorization check
        is_assignee = task.assignee_id == current_user_id
        is_creator = task.created_by == current_user_id
        is_project_owner = task.project.owner_id == current_user_id
        
        if not (is_assignee or is_creator or is_project_owner):
            raise ForbiddenException(
                message="You don't have permission to update task status"
            )
        
        old_status = task.status
        new_status = status_data.status
        
        # 🆕 STATE MACHINE: Validate transitions
        valid_transitions = {
            TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
            TaskStatus.IN_PROGRESS: [
                TaskStatus.IN_REVIEW,
                TaskStatus.BLOCKED,
                TaskStatus.DONE,
                TaskStatus.CANCELLED
            ],
            TaskStatus.IN_REVIEW: [
                TaskStatus.DONE,
                TaskStatus.IN_PROGRESS,
                TaskStatus.CANCELLED
            ],
            TaskStatus.BLOCKED: [
                TaskStatus.IN_PROGRESS,
                TaskStatus.CANCELLED
            ],
            TaskStatus.DONE: [TaskStatus.IN_PROGRESS],  # Can reopen
            TaskStatus.CANCELLED: [TaskStatus.TODO]  # Can reopen
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            raise BusinessLogicException(
                message=f"Invalid status transition from {old_status.value} to {new_status.value}",
                details={
                    "current_status": old_status.value,
                    "requested_status": new_status.value,
                    "valid_transitions": [s.value for s in valid_transitions[old_status]]
                }
            )
        
        # 🆕 Business Rules for specific transitions
        update_data = {"status": new_status}
        
        if new_status == TaskStatus.DONE:
            # Completing task
            if not task.actual_hours and not status_data.actual_hours:
                raise ValidationException(
                    message="Actual hours required when completing task",
                    details={"field": "actual_hours"}
                )
            
            update_data["completed_at"] = datetime.utcnow()
            
            if status_data.actual_hours:
                update_data["actual_hours"] = status_data.actual_hours
        
        if new_status == TaskStatus.BLOCKED:
            # Blocking task requires reason
            if not status_data.notes:
                raise ValidationException(
                    message="Reason required when blocking task",
                    details={"field": "notes"}
                )
            
            # TODO: Create blocking reason record
            # TODO: Notify project owner
        
        if new_status == TaskStatus.IN_PROGRESS and old_status == TaskStatus.TODO:
            # Starting task - check if assignee exists
            if not task.assignee_id:
                raise BusinessLogicException(
                    message="Cannot start unassigned task",
                    details={"hint": "Assign task first"}
                )
        
        # Update task
        updated_task = await self.task_repo.update(task_id, update_data)
        
        # 🆕 TODO: Trigger status change notifications
        # await self.notification_service.notify_status_change(task, old_status, new_status)
        
        # 🆕 Update project status if all tasks completed
        if new_status == TaskStatus.DONE:
            await self._check_project_completion(task.project_id)
        
        return await self.task_repo.get_with_relations(task_id)

    async def _check_project_completion(self, project_id: int) -> None:
        """
        🆕 CASCADING LOGIC: Check if project should be marked complete.
        
        Business Rule:
        If all tasks in a project are done, suggest project completion.
        """
        project = await self.project_repo.get_with_tasks(project_id)
        
        if not project.tasks:
            return
        
        all_done = all(
            task.status in [TaskStatus.DONE, TaskStatus.CANCELLED]
            for task in project.tasks
        )
        
        if all_done and project.status == ProjectStatus.ACTIVE:
            # TODO: Notify project owner to complete project
            # await self.notification_service.notify_project_ready_for_completion(project)
            pass

    async def assign_task(
        self,
        task_id: int,
        assignment_data: TaskAssignmentUpdate,
        current_user_id: int
    ) -> Task:
        """
        Assign or reassign task.
        
        🆕 Business Logic:
        - Only creator/project owner can assign
        - Check assignee availability
        - Notify new assignee
        - Log assignment history
        """
        task = await self.get_task(task_id, load_relations=True)
        
        # Authorization
        is_creator = task.created_by == current_user_id
        is_project_owner = task.project.owner_id == current_user_id
        
        if not (is_creator or is_project_owner):
            raise ForbiddenException(
                message="Only task creator or project owner can assign tasks"
            )
        
        new_assignee_id = assignment_data.assignee_id
        
        # Validate new assignee
        if new_assignee_id:
            assignee = await self.user_repo.get_by_id(new_assignee_id)
            if not assignee or not assignee.is_active:
                raise ValidationException(
                    message="Invalid assignee",
                    details={"assignee_id": new_assignee_id}
                )
            
            # 🆕 TODO: Check assignee workload
            # workload = await self._get_assignee_workload(new_assignee_id)
            # if workload.is_overloaded:
            #     # Warning: assignee is overloaded
            #     pass
        
        old_assignee_id = task.assignee_id
        
        # Update assignment
        updated_task = await self.task_repo.assign_task(task_id, new_assignee_id)
        
        # 🆕 TODO: Notifications
        # if old_assignee_id and old_assignee_id != new_assignee_id:
        #     await self.notification_service.notify_task_unassigned(old_assignee_id, task)
        # if new_assignee_id:
        #     await self.notification_service.notify_task_assigned(new_assignee_id, task)
        
        return await self.task_repo.get_with_relations(task_id)

    async def bulk_update_status(
        self,
        task_ids: List[int],
        new_status: TaskStatus,
        current_user_id: int
    ) -> Dict[str, Any]:
        """
        🆕 BULK OPERATIONS: Update multiple tasks at once.
        
        Advanced Concepts:
        - Transaction management (all or nothing)
        - Batch authorization checks
        - Partial success handling
        - Performance optimization
        
        PostgreSQL:
        - Single UPDATE with IN clause
        - Much faster than individual updates
        - Transaction ensures consistency
        """
        # Validate all tasks exist and user has permission
        tasks = await self.task_repo.get_by_ids(task_ids)
        
        if len(tasks) != len(task_ids):
            found_ids = {task.id for task in tasks}
            missing_ids = set(task_ids) - found_ids
            raise NotFoundException(
                message="Some tasks not found",
                details={"missing_ids": list(missing_ids)}
            )
        
        # Check permissions for all tasks
        unauthorized_tasks = []
        for task in tasks:
            is_authorized = (
                task.created_by == current_user_id or
                task.assignee_id == current_user_id or
                task.project.owner_id == current_user_id
            )
            if not is_authorized:
                unauthorized_tasks.append(task.id)
        
        if unauthorized_tasks:
            raise ForbiddenException(
                message="Not authorized to update some tasks",
                details={"unauthorized_task_ids": unauthorized_tasks}
            )
        
        # 🆕 TRANSACTION: Perform bulk update
        try:
            updated_count = await self.task_repo.bulk_update_status(
                task_ids,
                new_status
            )
            
            return {
                "success": True,
                "updated_count": updated_count,
                "task_ids": task_ids
            }
            
        except Exception as e:
            # Transaction will auto-rollback
            await self.db.rollback()
            raise BusinessLogicException(
                message="Bulk update failed",
                details={"error": str(e)}
            )

    async def delete_task(
        self,
        task_id: int,
        current_user_id: int
    ) -> bool:
        """Delete task (only creator or project owner)."""
        task = await self.get_task(task_id, load_relations=True)
        
        # Authorization
        is_creator = task.created_by == current_user_id
        is_project_owner = task.project.owner_id == current_user_id
        
        if not (is_creator or is_project_owner):
            raise ForbiddenException(
                message="Only task creator or project owner can delete tasks"
            )
        
        # Business Rule: Cannot delete completed tasks (optional)
        # This preserves historical data
        if task.status == TaskStatus.DONE:
            raise BusinessLogicException(
                message="Cannot delete completed tasks",
                details={"hint": "Use cancel instead"}
            )
        
        success = await self.task_repo.delete(task_id)
        
        return success

    async def get_project_tasks(
        self,
        project_id: int,
        status: Optional[TaskStatus] = None,
        assignee_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """Get all tasks for a project with filters."""
        tasks = await self.task_repo.get_by_project(
            project_id=project_id,
            skip=skip,
            limit=limit
        )
        
        # Apply filters
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if assignee_id:
            tasks = [t for t in tasks if t.assignee_id == assignee_id]
        
        return tasks

    async def get_user_tasks(
        self,
        user_id: int,
        status: Optional[TaskStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """Get all tasks assigned to a user."""
        return await self.task_repo.get_by_assignee(
            assignee_id=user_id,
            status=status,
            skip=skip,
            limit=limit
        )

    async def get_overdue_tasks(
        self,
        assignee_id: Optional[int] = None
    ) -> List[Task]:
        """Get all overdue tasks."""
        return await self.task_repo.get_overdue_tasks(assignee_id)

    async def get_task_statistics(
        self,
        project_id: Optional[int] = None,
        assignee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive task statistics.
        
        🆕 ADVANCED: Aggregated data from repository.
        """
        return await self.task_repo.get_task_statistics(
            project_id=project_id,
            assignee_id=assignee_id
        )

    async def get_high_priority_tasks(
        self,
        project_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Task]:
        """Get high priority tasks (for dashboard)."""
        return await self.task_repo.get_high_priority_tasks(
            project_id=project_id,
            limit=limit
        )