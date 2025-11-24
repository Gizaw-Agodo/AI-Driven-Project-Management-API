from typing import Any, Dict
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    message: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    
def create_error_response( message: str, status_code: int) -> Dict[str, Any]:
    response = ErrorResponse( message=message, status_code=status_code)
    return response.model_dump(exclude_none=True)