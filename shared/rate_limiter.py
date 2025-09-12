from fastapi import Request, HTTPException, status
from collections import defaultdict
import time

class RateLimiter:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client_requests = defaultdict(lambda: {'count': 0, 'last_reset': time.time()})
            cls._instance.default_limit = 100  # requests per minute
            cls._instance.default_period = 60    # seconds
        return cls._instance

    def _cleanup_expired_entries(self):
        now = time.time()
        expired_clients = [client_id for client_id, data in self.client_requests.items() if now - data['last_reset'] > self.default_period]
        for client_id in expired_clients:
            del self.client_requests[client_id]

    def check_rate_limit(self, client_id: str, limit: int = None, period: int = None):
        self._cleanup_expired_entries()

        current_limit = limit if limit is not None else self.default_limit
        current_period = period if period is not None else self.default_period

        client_data = self.client_requests[client_id]
        now = time.time()

        if now - client_data['last_reset'] > current_period:
            client_data['count'] = 1
            client_data['last_reset'] = now
        else:
            client_data['count'] += 1

        if client_data['count'] > current_limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        try:
            self.check_rate_limit(client_ip)
            response = await call_next(request)
            return response
        except HTTPException as exc:
            raise exc
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

def configure_rate_limiting(app):
    app.middleware("http")(RateLimiter())