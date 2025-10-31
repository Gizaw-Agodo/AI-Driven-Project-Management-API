from typing import Optional, List
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email_or_username( self, email: str, username: str) -> Optional[User]:
       
        query = select(User).where(or_(User.email == email, User.username == username))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def search_users(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        
        search_pattern = f"%{search_term}%"
        
        query = select(User).where(
            or_(
                User.email.ilike(search_pattern),
                User.username.ilike(search_pattern),
                User.full_name.ilike(search_pattern)
            )
        ).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list[User](result.scalars().all())
    
    async def get_user_with_projects(self, user_id : int )-> Optional[User]:
        query = select(User).where(User.id == user_id).options(
            selectinload(User.owned_projects)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_with_tasks(self, user_id: int) -> Optional[User]:
        query = select(User).where(User.id == user_id).options(
            selectinload(User.assigned_tasks),
            selectinload(User.created_tasks)
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def count_by_status(self, is_active:bool) -> int:
        query = select(func.count(User.id)).where(User.is_active == is_active)
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        query = select(User.id).where(User.email == email)
        
        if exclude_id:
            query = query.where(User.id != exclude_id)
        
        result = await self.db.execute(query)
        return result.first() is not None
    
    async def username_exists(
        self,
        username: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """Check if username exists."""
        query = select(User.id).where(User.username == username)
        
        if exclude_id:
            query = query.where(User.id != exclude_id)
        
        result = await self.db.execute(query)
        return result.first() is not None