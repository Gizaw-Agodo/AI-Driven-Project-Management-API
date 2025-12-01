from typing import Callable
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
class RequestIDMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        request.state.request_id = request_id
        response = await call_next(request)
        
        response.headers['X-Request-ID'] = request_id

        return response

def get_request_id(request:Request) -> str : 
    return getattr(request.state, "request_id", 'unknown')