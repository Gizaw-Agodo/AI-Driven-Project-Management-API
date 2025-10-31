from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
   
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(
        self,
        id: int,
        relationships: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        
        query = select(self.model).where(self.model.id == id)
        if relationships:
            for rel in relationships:
                query = query.options(selectinload(getattr(self.model, rel)))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_ids(
        self,
        ids: List[int],
        relationships: Optional[List[str]] = None
    ) -> List[ModelType]:
       
        query = select(self.model).where(self.model.id.in_(ids))
        
        if relationships:
            for rel in relationships:
                query = query.options(selectinload(getattr(self.model, rel)))
        
        result = await self.db.execute(query)
        return list[ModelType](result.scalars().all())

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        relationships: Optional[List[str]] = None
    ) -> List[ModelType]:

        query = select(self.model)
        
        # Eager loading
        if relationships:
            for rel in relationships:
                query = query.options(selectinload(getattr(self.model, rel)))
        
        # Ordering
        if order_by:
            if order_by.startswith('-'):
                # Descending order
                column = order_by[1:]
                query = query.order_by(getattr(self.model, column).desc())
            else:
                # Ascending order
                query = query.order_by(getattr(self.model, order_by))
        else:
            # Default: order by ID descending (newest first)
            query = query.order_by(self.model.id.desc())
        
        # Pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list[ModelType](result.scalars().all())

    async def get_by_filters(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        relationships: Optional[List[str]] = None
    ) -> List[ModelType]:
        query = select(self.model)
        
        # Apply filters
        for field, value in filters.items():
            if value is not None and hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        
        # Eager loading
        if relationships:
            for rel in relationships:
                query = query.options(selectinload(getattr(self.model, rel)))
        
        # Ordering
        if order_by:
            if order_by.startswith('-'):
                column = order_by[1:]
                query = query.order_by(getattr(self.model, column).desc())
            else:
                query = query.order_by(getattr(self.model, order_by))
        
        # Pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list[ModelType](result.scalars().all())

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
       
        query = select(func.count(self.model.id))
        
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:

        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)  
        return db_obj

    async def create_many(self, objects: List[Dict[str, Any]]) -> List[ModelType]:

        db_objects = [self.model(**obj) for obj in objects]
        self.db.add_all(db_objects)
        await self.db.commit()
        
        for obj in db_objects:
            await self.db.refresh(obj)
        
        return db_objects

    async def update(
        self,
        id: int,
        obj_in: Dict[str, Any],
        exclude_unset: bool = True
    ) -> Optional[ModelType]:

        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None
        
        for field, value in obj_in.items():
            if not exclude_unset or value is not None:
                setattr(db_obj, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_many(
        self,
        filters: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> int:
      
        query = update(self.model)
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        
        # Set new values
        query = query.values(**update_data)
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount

    async def delete(self, id: int) -> bool:
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return False
        
        await self.db.delete(db_obj)
        await self.db.commit()
        return True

    async def delete_many(self, ids: List[int]) -> int:

        query = delete(self.model).where(self.model.id.in_(ids))
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount

    async def exists(self, id: int) -> bool:
        query = select(self.model.id).where(self.model.id == id).limit(1)
        result = await self.db.execute(query)
        return result.first() is not None

    async def exists_by_field(self, field: str, value: Any) -> bool:
        if not hasattr(self.model, field):
            return False
        
        query = select(self.model.id).where(getattr(self.model, field) == value).limit(1)
        result = await self.db.execute(query)
        return result.first() is not None