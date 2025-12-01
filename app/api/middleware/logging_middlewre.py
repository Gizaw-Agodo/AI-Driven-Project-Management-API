import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware import P
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware): 
    SENSETIVE_HEADERS = [
        'authorization',
        'x-api-key',
        'cookie',
        'x-csrf-token'
    ]
    EXCLUDE_PATHS = [
        '/health',
        '/metrics'
    ]
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.EXCLUDE_PATHS:
           return await call_next(request)
        
        start_time  = time.time()
        request_info = self._extract_request_info(request)

        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )
        try: 
            response = await call_next(request)
        except Exception as e:
            process_time = time.time() - start_time
            
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": round(process_time, 3),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )
            raise

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(round(process_time, 3))
        
        # Log response
        log_level = self._get_log_level(response.status_code)
        
        logger.log(
            log_level,
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": round(process_time, 3),
                "response_size": response.headers.get("content-length", "unknown"),
            }
        )


    def _get_log_level(self, status_code: int) -> int:
        """
        Determine log level based on status code.
        
        🎓 LOG LEVEL STRATEGY:
        - 2xx: INFO (success)
        - 3xx: INFO (redirect)
        - 4xx: WARNING (client error)
        - 5xx: ERROR (server error)
        """
        if status_code < 400:
            return logging.INFO
        elif status_code < 500:
            return logging.WARNING
        else:
            return logging.ERROR

        

    
    async def _extract_request_info(self, request: Request) -> dict: 
        headers = {
            k:v for k, v in request.headers.items() if k.lower() not in self.SENSETIVE_HEADERS
        }

        return {
            "method" : request.method,
            "url" : str(request.url),
            "headers" : headers,
            "query_params": dict[str, str](request.query_params)
        }
