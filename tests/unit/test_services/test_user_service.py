"""
User service unit tests.

🎓 TESTING SERVICES:

Strategy:
- Mock repository layer
- Test business logic only
- Verify repository calls
- Test error cases
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserPasswordUpdate
from app.models.user import User
from app.utils.exceptions import (
    NotFoundException,
    AlreadyExistsException,
    UnauthorizedException,
    ValidationException
)


class TestUserServiceCreate:
    """Tests for user creation."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def user_service(self, mock_db):
        """Create service with mocked DB."""
        return UserService(mock_db)
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
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
    
    async def test_create_user_success(self, user_service, mock_user):
        """
        Test successful user creation.
        
        🎓 MOCKING PATTERN:
        
        1. Patch repository methods
        2. Set return values
        3. Call service method
        4. Assert results
        5. Verify mock calls
        """
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPass123",
            full_name="Test User"
        )
        
        # Mock repository methods
        with patch.object(
            user_service.user_repo,
            'email_exists',
            new_callable=AsyncMock,
            return_value=False
        ) as mock_email_exists, \
        patch.object(
            user_service.user_repo,
            'username_exists',
            new_callable=AsyncMock,
            return_value=False
        ) as mock_username_exists, \
        patch.object(
            user_service.user_repo,
            'create',
            new_callable=AsyncMock,
            return_value=mock_user
        ) as mock_create:
            
            # Call service
            result = await user_service.create_user(user_data)
            
            # Assertions
            assert result == mock_user
            
            # Verify mocks were called correctly
            mock_email_exists.assert_called_once_with("test@example.com")
            mock_username_exists.assert_called_once_with("testuser")
            mock_create.assert_called_once()
    
    async def test_create_user_duplicate_email(self, user_service):
        """
        Test user creation with duplicate email.
        
        🎓 TESTING EXCEPTIONS:
        
        Use pytest.raises() to test expected exceptions.
        """
        user_data = UserCreate(
            email="existing@example.com",
            username="newuser",
            password="TestPass123",
            full_name="Test User"
        )
        
        # Mock email already exists
        with patch.object(
            user_service.user_repo,
            'email_exists',
            new_callable=AsyncMock,
            return_value=True  # Email exists
        ):
            # Should raise exception
            with pytest.raises(AlreadyExistsException) as exc_info:
                await user_service.create_user(user_data)
            
            # Verify exception details
            assert "email" in exc_info.value.details.get("field", "")
    
    async def test_create_user_duplicate_username(self, user_service):
        """Test user creation with duplicate username."""
        user_data = UserCreate(
            email="new@example.com",
            username="existinguser",
            password="TestPass123",
            full_name="Test User"
        )
        
        with patch.object(
            user_service.user_repo,
            'email_exists',
            new_callable=AsyncMock,
            return_value=False
        ), \
        patch.object(
            user_service.user_repo,
            'username_exists',
            new_callable=AsyncMock,
            return_value=True  # Username exists
        ):
            with pytest.raises(AlreadyExistsException) as exc_info:
                await user_service.create_user(user_data)
            
            assert "username" in exc_info.value.details.get("field", "")


class TestUserServiceAuthentication:
    """Tests for user authentication."""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def user_service(self, mock_db):
        return UserService(mock_db)
    
    @pytest.fixture
    def mock_active_user(self):
        """Mock active user with correct password."""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        # This is the hash of "TestPass123"
        from app.core.security import hash_password
        user.hashed_password = hash_password("TestPass123")
        user.is_active = True
        return user
    
    async def test_authenticate_success_with_email(
        self,
        user_service,
        mock_active_user
    ):
        """
        Test successful authentication with email.
        
        🎓 TESTING HAPPY PATH:
        
        Always test the successful case first!
        """
        with patch.object(
            user_service.user_repo,
            'get_by_email',
            new_callable=AsyncMock,
            return_value=mock_active_user
        ):
            result = await user_service.authenticate_user(
                email_or_username="test@example.com",
                password="TestPass123"
            )
            
            assert result == mock_active_user
    
    async def test_authenticate_success_with_username(
        self,
        user_service,
        mock_active_user
    ):
        """Test successful authentication with username."""
        with patch.object(
            user_service.user_repo,
            'get_by_username',
            new_callable=AsyncMock,
            return_value=mock_active_user
        ):
            result = await user_service.authenticate_user(
                email_or_username="testuser",  # No @ = username
                password="TestPass123"
            )
            
            assert result == mock_active_user
    
    async def test_authenticate_user_not_found(self, user_service):
        """
        Test authentication with non-existent user.
        
        🎓 SECURITY TESTING:
        
        Verify generic error messages (don't reveal if user exists).
        """
        with patch.object(
            user_service.user_repo,
            'get_by_email',
            new_callable=AsyncMock,
            return_value=None  # User not found
        ):
            with pytest.raises(UnauthorizedException) as exc_info:
                await user_service.authenticate_user(
                    email_or_username="notfound@example.com",
                    password="TestPass123"
                )
            
            # Generic message (security)
            assert "Invalid credentials" in exc_info.value.message
    
    async def test_authenticate_wrong_password(
        self,
        user_service,
        mock_active_user
    ):
        """Test authentication with wrong password."""
        with patch.object(
            user_service.user_repo,
            'get_by_email',
            new_callable=AsyncMock,
            return_value=mock_active_user
        ):
            with pytest.raises(UnauthorizedException):
                await user_service.authenticate_user(
                    email_or_username="test@example.com",
                    password="WrongPassword123"  # Wrong password
                )
    
    async def test_authenticate_inactive_user(self, user_service):
        """Test authentication with inactive user."""
        inactive_user = MagicMock(spec=User)
        inactive_user.id = 1
        inactive_user.email = "test@example.com"
        from app.core.security import hash_password
        inactive_user.hashed_password = hash_password("TestPass123")
        inactive_user.is_active = False  # Inactive!
        
        with patch.object(
            user_service.user_repo,
            'get_by_email',
            new_callable=AsyncMock,
            return_value=inactive_user
        ):
            with pytest.raises(UnauthorizedException) as exc_info:
                await user_service.authenticate_user(
                    email_or_username="test@example.com",
                    password="TestPass123"
                )
            
            assert "inactive" in exc_info.value.message.lower()


class TestUserServicePasswordChange:
    """Tests for password change functionality."""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def user_service(self, mock_db):
        return UserService(mock_db)
    
    async def test_change_password_success(self, user_service):
        """Test successful password change."""
        from app.core.security import hash_password
        
        # Mock user with known password
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.hashed_password = hash_password("OldPass123")
        
        password_data = UserPasswordUpdate(
            current_password="OldPass123",
            new_password="NewPass123",
            confirm_password="NewPass123"
        )
        
        with patch.object(
            user_service,
            'get_user_by_id',
            new_callable=AsyncMock,
            return_value=mock_user
        ), \
        patch.object(
            user_service.user_repo,
            'update',
            new_callable=AsyncMock,
            return_value=mock_user
        ) as mock_update:
            result = await user_service.change_password(
                user_id=1,
                password_data=password_data
            )
            
            # Verify update was called with new hashed password
            mock_update.assert_called_once()
            call_args = mock_update.call_args[0]
            assert "hashed_password" in call_args[1]
    
    async def test_change_password_wrong_current(self, user_service):
        """Test password change with wrong current password."""
        from app.core.security import hash_password
        
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.hashed_password = hash_password("OldPass123")
        
        password_data = UserPasswordUpdate(
            current_password="WrongPass123",  # Wrong!
            new_password="NewPass123",
            confirm_password="NewPass123"
        )
        
        with patch.object(
            user_service,
            'get_user_by_id',
            new_callable=AsyncMock,
            return_value=mock_user
        ):
            with pytest.raises(UnauthorizedException):
                await user_service.change_password(
                    user_id=1,
                    password_data=password_data
                )
    
    async def test_change_password_same_as_current(self, user_service):
        """Test password change with same password."""
        from app.core.security import hash_password
        
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.hashed_password = hash_password("SamePass123")
        
        password_data = UserPasswordUpdate(
            current_password="SamePass123",
            new_password="SamePass123",  # Same as current!
            confirm_password="SamePass123"
        )
        
        with patch.object(
            user_service,
            'get_user_by_id',
            new_callable=AsyncMock,
            return_value=mock_user
        ):
            with pytest.raises(ValidationException):
                await user_service.change_password(
                    user_id=1,
                    password_data=password_data
                )