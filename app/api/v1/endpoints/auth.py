from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import Token, LoginResponse, TokenRefreshRequest
from app.schemas.user import UserCreate, UserResponse
from app.core.security import (
    create_token_pair,
    decode_token,
    verify_token_type
)
from app.core.config import settings
from app.services import user_service
from app.services.user_service import UserService
from app.api.deps import get_db, get_user_service, get_current_user
from app.models.user import User


router = APIRouter()


# ==================== REGISTER ====================
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account"
)
async def register(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    user = await user_service.create_user(user_data)
    return user


# ==================== LOGIN ====================
@router.post(
    "/login",
    response_model=Token,
    summary="Login to get access token",
    description="Authenticate with username/email and password to receive JWT tokens"
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserService = Depends(get_user_service)
) -> Token:

    # Authenticate user
    user = await user_service.authenticate_user(
        email_or_username=form_data.username,
        password=form_data.password
    )
    
    # Create token pair
    tokens = create_token_pair(
        user_id=user.id,
        username=user.username,
        email=user.email
    )
    
    return Token(
        access_token=tokens["access_token"],
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        refresh_token=tokens["refresh_token"]
    )


@router.post(
    "/login/enhanced",
    response_model=LoginResponse,
    summary="Login with user data",
    description="Login and receive tokens + user profile in one response"
)
async def login_enhanced(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserService = Depends(get_user_service)
) -> LoginResponse:
    
    # Authenticate
    user = await user_service.authenticate_user(
        email_or_username=form_data.username,
        password=form_data.password
    )
    
    # Create tokens
    tokens = create_token_pair(
        user_id=user.id,
        username=user.username,
        email=user.email
    )
    
    # Convert user to dict (exclude password)
    from app.schemas.user import UserResponse
    user_response = UserResponse.model_validate(user)
    
    return LoginResponse(
        access_token=tokens["access_token"],
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=tokens["refresh_token"],
        user=user_response.model_dump()
    )


# ==================== TOKEN REFRESH ====================

@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Get a new access token using refresh token"
)
async def refresh_token(
    refresh_request: TokenRefreshRequest,
    user_service: UserService = Depends(get_user_service)
) -> Token:
   
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode refresh token
        payload = decode_token(refresh_request.refresh_token)
        
        if payload is None:
            raise credentials_exception
        
        # 🎓 SECURITY: Verify this is a refresh token
        if not verify_token_type(payload, "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Refresh token required.",
            )
        
        # Extract user info
        user_id_str = payload.get("sub")
        
        if not user_id_str:
            raise credentials_exception
        
        user_id = int(user_id_str)

        user = await user_service.get_user_by_id(user_id)
    
        if not user or not user.is_active:
            raise credentials_exception

        tokens = create_token_pair(
            user_id=user.id,
            username=user.username,
            email=user.email
        )
        
        return Token(
            access_token=tokens["access_token"],
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=tokens["refresh_token"]  # New refresh token
        )
        
    except Exception:
        raise credentials_exception
    
    


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Logout current user (client should delete tokens)"
)
async def logout(
    current_user: User = Depends(get_current_user)
):
    # TODO: Implement token blacklist if needed
    # For now, client-side logout is sufficient
    
    # Could log logout event
    # logger.info(f"User {current_user.id} logged out")
    
    return  # 204 No Content


# ==================== VERIFY TOKEN ====================

@router.get(
    "/verify",
    response_model=UserResponse,
    summary="Verify token",
    description="Verify current token and return user data"
)
async def verify_current_token(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    
    return current_user


# ==================== TEST ENDPOINTS ====================

@router.get(
    "/test/public",
    summary="Test public endpoint",
    description="Public endpoint that doesn't require authentication"
)
async def test_public():
    """
    Test endpoint - no authentication required.
    
    🎓 TESTING:
    Use this to verify API is working.
    """
    return {
        "message": "This is a public endpoint",
        "authenticated": False
    }


@router.get(
    "/test/protected",
    summary="Test protected endpoint",
    description="Protected endpoint that requires authentication"
)
async def test_protected(
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint - authentication required.
    
    🎓 TESTING:
    Use this to verify tokens work.
    
    Should return 401 if:
    - No Authorization header
    - Invalid token
    - Expired token
    
    Should return user data if valid token.
    """
    return {
        "message": "This is a protected endpoint",
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        }
    }