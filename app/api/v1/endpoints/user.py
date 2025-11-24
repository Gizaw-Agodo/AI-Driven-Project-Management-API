from fastapi import APIRouter, Depends, status, Query, Path, Body

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserWithStats,
    UserPasswordUpdate,
    UserListResponse
)
from app.schemas.base import PaginationParams
from app.models.user import User
from app.services.user_service import UserService
from app.api.deps import (
    get_db,
    get_current_user,
    get_current_superuser,
    get_user_service
)


router = APIRouter()


# ==================== CREATE OPERATIONS ====================

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Register a new user account with email and password"
)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    user = await user_service.create_user(user_data)
    return user


# ==================== READ OPERATIONS ====================
@router.get(
    "/",
    response_model=UserListResponse,
    summary="List all users",
    description="Get paginated list of all users (admin only)"
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)  # 🎓 Admin only
) -> UserListResponse:
    
    users = await user_service.get_all()
    return UserListResponse(users=users)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's profile"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    return current_user


@router.get(
    "/me/stats",
    response_model=UserWithStats,
    summary="Get current user with statistics",
    description="Get current user profile with project and task statistics"
)
async def get_current_user_stats(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    
    stats = await user_service.get_user_statistics(current_user.id)
    
    # Combine user and stats
    user_with_stats = UserWithStats(
        **current_user.__dict__,
        total_projects=stats["total_projects"],
        total_tasks=stats["total_assigned_tasks"],
        completed_tasks=stats["completed_tasks"]
    )
    
    return user_with_stats


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Get a specific user by their ID"
)
async def get_user(
    user_id: int = Path(..., gt=0, description="User ID"),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    user = await user_service.get_user_by_id(user_id)
    return user


# ==================== UPDATE OPERATIONS ====================

@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update the currently authenticated user's profile"
)
async def update_current_user(
    user_data: UserUpdate = Body(..., description="User update data"),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    
    updated_user = await user_service.update_user(
        user_id=current_user.id,
        user_data=user_data,
        current_user_id=current_user.id
    )
    return updated_user


@router.put(
    "/me/password",
    response_model=UserResponse,
    summary="Change password",
    description="Change the current user's password"
)
async def change_password(
    password_data: UserPasswordUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    updated_user = await user_service.change_password(
        user_id=current_user.id,
        password_data=password_data
    )
    return updated_user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user (admin)",
    description="Update any user's profile (admin only)"
)
async def update_user(
    user_id: int = Path(..., gt=0),
    user_data: UserUpdate = Body(...),
    user_service: UserService = Depends(get_user_service),
    admin: User = Depends(get_current_user)  # 🎓 Admin only
) -> UserResponse:
    updated_user = await user_service.update_user(
        user_id=user_id,
        user_data=user_data,
        current_user_id=admin.id
    )
    return updated_user


# ==================== DELETE OPERATIONS ====================

@router.post(
    "/me/deactivate",
    response_model=UserResponse,
    summary="Deactivate account",
    description="Deactivate the current user's account (soft delete)"
)
async def deactivate_account(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    deactivated_user = await user_service.deactivate_user(current_user.id)
    return deactivated_user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user (admin)",
    description="Permanently delete a user (admin only)"
)
async def delete_user(
    user_id: int = Path(..., gt=0),
    user_service: UserService = Depends(get_user_service),
    admin: User = Depends(get_current_superuser)
):

    await user_service.delete_user(user_id)