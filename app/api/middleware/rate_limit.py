from ast import Tuple
from collections import defaultdict
import time
from typing import Callable
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute:int = 60, requests_per_hour: int = 1600) -> None:
        super().__init__(app)
    
        self.request_per_minute = requests_per_minute
        self.request_per_hour = requests_per_hour
        self.trusted_proxies = {'1.2.3.4', '3.4.5.6'}
        self.excluded_paths = {'/health','/metrices'}

        self.requests : dict[str, list] = defaultdict[str, list](list)

    async def dispatch(self, request: Request, call_next : Callable):
        client_ip = self._get_client_ip(request)

        if self._should_skip_rate_limit(request):
            return await call_next(request)
        
        current_time = time.time()
        self._cleanup_old_requests(client_ip, current_time)
        minute_count, hour_count = self._get_request_count(client_ip, current_time)

        if minute_count >= self.request_per_minute : 
            reset_time = self._calculate_reset_time(client_ip, window = 60)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Too many requests per minute.",
                headers={
                    "X-RateLimit-Limit": str(self.request_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(int(reset_time - current_time)),
                }
            )

        if hour_count >= self.request_per_hour:
            reset_time = self._calculate_reset_time(client_ip, window=3600)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Too many requests per hour.",
                headers={
                    "X-RateLimit-Limit": str(self.request_per_hour),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(int(reset_time - current_time)),
                }
            )

        self.requests[client_ip].append(current_time)
        response = await call_next(request)

        remaining_minute = self.request_per_minute - minute_count - 1
        remaining_hour = self.request_per_hour - hour_count - 1
        
        response.headers["X-RateLimit-Limit-Minute"] = str(self.request_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, remaining_minute))
        response.headers["X-RateLimit-Limit-Hour"] = str(self.request_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(max(0, remaining_hour))
        
        return response

    
    def _get_client_ip(self,request : Request) -> str:

        remote_addr = request.client.host if request.client else "unknown"
        
        if remote_addr not in self.trusted_proxies:
            return remote_addr

        forwareded_for = request.headers.get("X-Forwarded-For")
        if forwareded_for:
            return forwareded_for.split(',')[0].strip()
    
    def _should_skip_rate_limit(self, request : Request)-> bool: 
        if request.url.path in self.excluded_paths:
            return True
        return False

    
    def _cleanup_old_requests(self, client_ip:str, current_time: float):
        """remove requests more than one hour"""
        if client_ip in self.requests:
            self.requests[client_ip] = [t for t in self.requests[client_ip] if t > current_time - 3600]
    
    def _get_request_count(self, client_ip: str, current_time : float) -> Tuple[int, int]:
        if client_ip not in self.requests: 
            return (0,0)
        
        one_minute_ago = current_time - 60 
        one_hour_ago  = current_time - 3600

        timestamps = self.requests[client_ip]

        minutes_count = sum(1 for t in timestamps if t > one_minute_ago)
        hours_count = sum(1 for t in timestamps if t > one_hour_ago)

        return (minutes_count, hours_count)

    def _calculate_reset_time(self, client_ip: str, window : int ) -> float:
        if client_ip not in self.requests: 
            return time.time()
        
        oldest_request = min(self.requests[client_ip])
        return oldest_request + window

