import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from server.core.redis import redis_client
from server.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.whitelist_ips = ["127.0.0.1", "::1"]  # Add your whitelist
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        if request.client:
            client_ip = request.client.host
        else:
            client_ip = "unknown"
        
        # Skip rate limiting for whitelisted IPs
        if client_ip in self.whitelist_ips:
            return await call_next(request)
        
        # Skip rate limiting for certain paths
        excluded_paths = [
            "/docs", "/redoc", "/openapi.json",
            "/health", "/favicon.ico"
        ]
        
        if any(request.url.path.startswith(path) for path in excluded_paths):
            return await call_next(request)
        
        # Create rate limit keys
        current_minute = int(time.time() / 60)
        current_hour = int(time.time() / 3600)
        
        minute_key = f"rate_limit:{client_ip}:minute:{current_minute}"
        hour_key = f"rate_limit:{client_ip}:hour:{current_hour}"
        
        try:
            # Check minute rate limit
            minute_count = await redis_client.get(minute_key)
            if minute_count and int(minute_count) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Too many requests",
                        "message": "Please try again in a minute.",
                        "retry_after": 60
                    }
                )
            
            # Check hour rate limit
            hour_count = await redis_client.get(hour_key)
            if hour_count and int(hour_count) >= self.requests_per_hour:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Too many requests",
                        "message": "Please try again in an hour.",
                        "retry_after": 3600
                    }
                )
            
            # Increment counters using pipeline for atomic operations
            pipe = redis_client.pipeline()
            pipe.incr(minute_key, 1)
            pipe.expire(minute_key, 60)  # Expire after 60 seconds
            pipe.incr(hour_key, 1)
            pipe.expire(hour_key, 3600)  # Expire after 1 hour
            await pipe.execute()
            
        except Exception as e:
            # If Redis fails, log but allow the request
            import logging
            logging.error(f"Rate limit Redis error: {e}")
            # Continue without rate limiting if Redis is down
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        
        if minute_count:
            remaining_minute = max(0, self.requests_per_minute - int(minute_count))
            response.headers["X-RateLimit-Remaining-Minute"] = str(remaining_minute)
        
        if hour_count:
            remaining_hour = max(0, self.requests_per_hour - int(hour_count))
            response.headers["X-RateLimit-Remaining-Hour"] = str(remaining_hour)
        
        return response