from turtle import update
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserPasswordUpdate
from app.models.user import User
from app.core.security import hash_password, verify_password
from app.utils.exceptions import ( ForbiddenException, NotFoundException, AlreadyExistsException, UnauthorizedException, ValidationException, BusinessLogicException)
class UserService:
    def __init(self, db: AsyncSession):
        self.db = db 
        self.user_repo = UserRepository(db)
   
    async def create_user(self, user_data: UserCreate) -> User:

        # email must be unique 
        if await self.user_repo.email_exists(user_data.email):
            raise AlreadyExistsException(
                message="Email already registered", 
                details= {
                    "field":"email", 
                    "value" : user_data.email
                }
            )
        # username must be unique 
        if await self.user_repo.username_exists(user_data.username):
            raise AlreadyExistsException(
                message="username already taken", 
                details= {
                    "field":"username", 
                    "value": user_data.username
                }
            )
        
        try:
            #hash password 
            hashed_password = hash_password(user_data.password)
            user_dict = user_data.model_dump(exclude={"password"})
            user_dict["hashed_password"] = hashed_password

            user = await self.user_repo.create(user_dict)
            return user

        except IntegrityError as e : 
            await self.db.rollback()
            raise AlreadyExistsException( message = "user already exists")
        
    async def get_user_by_id(self, user_id : int, load_relations : bool = False):
        if load_relations:
            user = await self.user_repo.get_user_with_projects(user_id)
        else: 
            user = await self.user_repo.get_by_id(user_id)
        
        if not user:
            raise NotFoundException(
                message=f'User with ID {user_id} not found', 
                details= { "user_id" : user_id }
            )
        return user 

    async def get_user_by_email(self, user_email: str): 
        user = await self.user_repo.get_by_email(user_email)
        if not user : 
            raise NotFoundException(
                message=f"User with email {user_email} not found"
            )
        return user 
    
    async def get_user_by_username(self, username: str): 
        user = await self.user_repo.get_by_username(username)
        if not user : 
            raise NotFoundException(
                message = f"User with username {username} not found"
            )
        return user
    
    async def authenticate_user(self, email : str, passowrd: str) -> User: 
        user = await self.user_repo.get_by_email(email)

        if not user: 
            raise UnauthorizedException(message="Invalid credentials")
        
        if not verify_password(passowrd, user.hashed_password):
            raise UnauthorizedException(message="Invalide credentials")
        
        if not user.is_active:
            raise UnauthorizedException(message = "User is inactive")
        
        return user
    
    async def update_user(self, user_id: int , user_data : UserUpdate, current_user_id: int)-> User:
        user = await self.user_repo.get_by_id(user_id)

        if not user : 
            raise NotFoundException("User with this id not found")
        
        if user.id != current_user_id:
            raise ForbiddenException("You can only update your own profile")
        
        if user_data.email and user_data.email != user.email:
            if self.user_repo.email_exists(user_data.email):
                raise AlreadyExistsException(message="Email already exists")
        
        if user_data.username and user_data.username != user.username:
            if self.user_repo.username_exists(user_data.username):
                raise AlreadyExistsException(message = "Username already exists")
        
        update_dict = user_data.model_dump(exclude_unset=True)
        updated_user = await self.user_repo.update(user_id,update_dict )
        return updated_user
    

    async def change_password(self,user_id : int, password_data : UserPasswordUpdate ):
        user = await self.user_repo.get_by_id(user_id)

        if not verify_password(password_data.current_password, user.hashed_password):
            raise UnauthorizedException("Current password is incorrect")
        
        if password_data.new_password == password_data.current_password:
            raise ValidationException("New password must be different")

        hashed_password = hash_password(password_data.current_password)
        updated_user = await self.user_repo.update(user_id,{"hashed_password": hashed_password})

        return updated_user
    
    async def deactivate_user(self, user_id: int):
        user = await self.get_user_by_id(user_id)

        if not user.is_active:
            raise BusinessLogicException("user is already inactive")
        
        updated_user = self.user_repo.update(user_id , {"is_active": False})
        return updated_user
    
    async def activate_user(self, user_id: int):
        user = await self.get_user_by_id(user_id)

        if  user.is_active:
            raise BusinessLogicException("user is already active")
        
        updated_user = self.user_repo.update(user_id , {"is_active": True})
        return updated_user

    
    async def delete_user(self, user_id: int) -> bool:
        user = await self.get_user_by_id(user_id)
        
        if user.is_superuser:
            raise BusinessLogicException(message="Cannot delete superuser accounts" )
        
        success = await self.user_repo.delete(user_id)
        
        if not success:
            raise NotFoundException( message=f"Failed to delete user {user_id}")
        
        return success


    