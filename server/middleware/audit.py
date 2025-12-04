# server/middleware/audit.py

import json
import time
from typing import ASGIApp
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.app = app

    async def dispatch(self, request: Request, call_next):
        # Cek apakah request ke path yang tidak perlu diaudit
        if request.url.path in [
            "/docs", "/redoc", "/openapi.json", "/health", 
            "/status", "/favicon.ico"
        ]:
            return await call_next(request)

        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Hanya log request yang sukses
            if 200 <= response.status_code < 300:
                self._log_request(request, response, process_time)
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            self._log_error(request, e, process_time)
            
            # Re-raise exception agar FastAPI bisa menanganinya
            raise

    def _log_request(self, request: Request, response: Response, process_time: float):
        """Log request yang sukses."""
        log_entry = {
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": process_time,
            "timestamp": time.time(),
            "user_agent": request.headers.get("user-agent"),
            "remote_addr": request.client.host if request.client else None,
        }
        print(f"AUDIT: {json.dumps(log_entry)}")

    def _log_error(self, request: Request, error: Exception, process_time: float):
        """Log error."""
        log_entry = {
            "method": request.method,
            "url": str(request.url),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "process_time": process_time,
            "timestamp": time.time(),
            "user_agent": request.headers.get("user-agent"),
            "remote_addr": request.client.host if request.client else None,
        }
        print(f"AUDIT ERROR: {json.dumps(log_entry)}")