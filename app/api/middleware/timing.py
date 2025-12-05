import time 
import logging
from typing import Callable 
from fastapi import Request, Response

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class TimingMiddleware(BaseHTTPMiddleware): 
    def __init__(self, app, slow_request_threshold:float = 1.0) -> None:
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold


    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        request.state.start_time = start_time
        response = await call_next(request)
        duration = time.time() - start_time

        response.headers["X-Process-Time"] = f"{duration:.3f}"
        
        # 🎓 PERFORMANCE ALERTING
        if duration > self.slow_request_threshold:
            logger.warning(
                f"Slow request: {request.method} {request.url.path}",
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "method": request.method,
                    "path": request.url.path,
                    "duration": round(duration, 3),
                    "threshold": self.slow_request_threshold,
                }
            )
            
        return response
