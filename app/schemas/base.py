from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional


class BaseSchema(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,  
        populate_by_name=True,
        str_strip_whitespace=True,  
        use_enum_values=True,  
    )


class TimestampSchema(BaseSchema):

    created_at: datetime
    updated_at: datetime



class IDSchema(BaseSchema):
    id: int = Field(..., gt=0, description="Unique identifier")


class PaginationParams(BaseModel):

    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Max records to return")
    

class PaginatedResponse(BaseModel):

    total: int = Field(..., description="Total number of records")
    skip: int
    limit: int
    data: list
    
    @property
    def has_more(self) -> bool:
        return self.total > (self.skip + self.limit)