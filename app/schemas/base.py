from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, 
        populate_by_name=True, 
        str_strip_whitespace=True,
        use_enum_values=True
    )

class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at : datetime

class IDSchema(BaseSchema):
    id : int = Field(..., gt = 0)

class PaginationParams(BaseModel): 
    skip: int = Field(0, ge = 0)
    limit: int = Field(100, ge=1, le= 1000)

class PaginationResponse(BaseModel): 
    total : int
    skip: int
    limit: int
    data : list