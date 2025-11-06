from typing import Optional, Any


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found exception."""
    
    def __init__(self, message: str = "Resource not found", details: Optional[dict] = None):
        super().__init__(message, status_code=404, details=details)


class AlreadyExistsException(AppException):
    """Resource already exists exception."""
    
    def __init__(self, message: str = "Resource already exists", details: Optional[dict] = None):
        super().__init__(message, status_code=409, details=details)


class ValidationException(AppException):
    """Validation error exception."""
    
    def __init__(self, message: str = "Validation error", details: Optional[dict] = None):
        super().__init__(message, status_code=422, details=details)


class UnauthorizedException(AppException):
    """Authentication failed exception."""
    
    def __init__(self, message: str = "Unauthorized", details: Optional[dict] = None):
        super().__init__(message, status_code=401, details=details)


class ForbiddenException(AppException):
    """Permission denied exception."""
    
    def __init__(self, message: str = "Forbidden", details: Optional[dict] = None):
        super().__init__(message, status_code=403, details=details)


class BadRequestException(AppException):
    """Bad request exception."""
    
    def __init__(self, message: str = "Bad request", details: Optional[dict] = None):
        super().__init__(message, status_code=400, details=details)


class DatabaseException(AppException):
    """Database operation exception."""
    
    def __init__(self, message: str = "Database error", details: Optional[dict] = None):
        super().__init__(message, status_code=500, details=details)


class BusinessLogicException(AppException):
    """Business logic validation exception."""
    
    def __init__(self, message: str = "Bad request", details: Optional[dict] = None):
        super().__init__(message, status_code=400, details=details)