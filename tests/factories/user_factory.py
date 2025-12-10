from faker import Faker
from app.models.user import User
from app.core.security import hash_password
from typing import Optional

fake = Faker()


class UserFactory:
    
    @staticmethod
    def create(
        email: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None, 
        full_name: Optional[str] = None,
        is_active: bool = True,
        is_superuser: bool = False,
    ) -> User:
        """Create a User model instance with a random password if not provided."""
        
        return User(
            email=email or fake.email(),
            username=username or fake.user_name()[:20],
            hashed_password=hash_password(password or fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)),
            full_name=full_name or fake.name(),
            is_active=is_active,
            is_superuser=is_superuser,
        )

    @staticmethod
    def create_dict(
        email: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,  
        full_name: Optional[str] = None,
    ) -> dict:
        """Create dict for API requests with random password if not provided."""
        return {
            "email": email or fake.email(),
            "username": username or fake.user_name()[:20],
            "password": password or fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
            "full_name": full_name or fake.name(),
        }

    @staticmethod
    def create_batch(count: int, **kwargs) -> list[User]:
        """Create multiple users."""
        return [UserFactory.create(**kwargs) for _ in range(count)]
