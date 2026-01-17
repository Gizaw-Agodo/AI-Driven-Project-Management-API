
import pytest
from unittest.mock import AsyncMock , MagicMock, patch

from datetime import datetime

from app.services import UserService
from app.schemas import UserCreate, UserUpdate, UserPasswordUpdate
from app.models import User
from app.utils.exceptions import (
    NotFoundException, 
    AlreadyExistsException, 
    UnauthorizedException, 
    ValidationException
)

class TestUserServiceCreate:
    
    @pytest.fixture
    def mock_repo(self):
        return MagicMock()
    
    @pytest.fixture
    def user_service(self, mock_repo):
        return UserService(user_repo = mock_repo)
    
    @pytest.fixture
    def mock_user(self):
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.hashed_password = "hashed"
        user.is_active = True
        user.is_superuser = False
        user.created_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        return user
    
    async def test_create_user_success(self, user_service, mock_user, mock_repo): 
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPass123",
            full_name="Test User"
        )

        mock_repo.email_exists = AsyncMock(return_value = False)
        mock_repo.username_exists = AsyncMock(return_value = False)
        mock_repo.create = AsyncMock(return_value = mock_user)

        #act
        result = await user_service.create_user(user_data)

        #assert
        assert result == mock_user

        #verify
        mock_repo.email_exists.assert_called_once_with("test@example.com")
        mock_repo.username_exists.assert_called_once_with("testuser")
        mock_repo.create.assert_called_once()

    async def test_create_user_duplicate_email(self, user_service, mock_repo):
        user_data = UserCreate(
            email="existing@example.com",
            username="newuser",
            password="TestPass123",
            full_name="Test User"
        )

        mock_repo.email_exists = AsyncMock(return_value = True)

        #act & assert
        with pytest.raises(AlreadyExistsException) as exc_info:
            await user_service.create_user(user_data)
    
        





