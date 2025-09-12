from fastapi import Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

from security.auth import ALGORITHM, SECRET_KEY, get_current_user
from security.api_key_manager import APIKeyManager
from shared.error_handling import ErrorResponse, ErrorHandler

class AuthMiddleware:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
            cls._instance.api_key_manager = APIKeyManager()
            cls._instance.error_handler = ErrorHandler()
        return cls._instance

    async def __call__(self, request: Request, call_next):
        try:
            # Skip authentication for specific paths (e.g., docs, health checks)
            if request.url.path in ["/docs", "/redoc", "/openapi.json", "/health"]:
                response = await call_next(request)
                return response

            # JWT Authentication
            if "authorization" in request.headers:
                token = request.headers["authorization"].split(" ")[1]
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username: str = payload.get("sub")
                if username is None:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
                request.state.user = await get_current_user(token) # Assuming get_current_user fetches user details

            # API Key Authentication
            elif "x-api-key" in request.headers:
                api_key = request.headers["x-api-key"]
                if not self.api_key_manager.validate_api_key(api_key):
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
                # Optionally, associate API key with a user or permissions
                request.state.api_key_user = self.api_key_manager.get_user_from_api_key(api_key)

            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

            response = await call_next(request)
            return response
        except JWTError:
            return self.error_handler.handle_exception(request, HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"))
        except HTTPException as exc:
            return self.error_handler.handle_exception(request, exc)
        except Exception as exc:
            return self.error_handler.handle_exception(request, HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"))

def configure_auth_middleware(app):
    app.middleware("http")(AuthMiddleware())