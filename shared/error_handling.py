import logging
import traceback
from typing import Dict, Any, Optional, Callable, Type
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger("error_handler")

class ErrorResponse(BaseModel):
    """Standardized error response model"""
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None

class ErrorHandler:
    """Centralized error handling for all MCP servers"""
    
    def __init__(self):
        self.error_codes = {
            "AUTHENTICATION_ERROR": "Authentication failed or not provided",
            "AUTHORIZATION_ERROR": "Insufficient permissions for this operation",
            "VALIDATION_ERROR": "Invalid input data",
            "RESOURCE_NOT_FOUND": "Requested resource not found",
            "SERVER_ERROR": "Internal server error",
            "DEPENDENCY_ERROR": "Error in dependent service",
            "RATE_LIMIT_ERROR": "Rate limit exceeded",
            "TIMEOUT_ERROR": "Operation timed out",
            "CONFLICT_ERROR": "Resource conflict",
            "BAD_REQUEST": "Invalid request"
        }
        
        # Map exception types to error codes
        self.exception_mapping: Dict[Type[Exception], str] = {
            ValueError: "VALIDATION_ERROR",
            KeyError: "RESOURCE_NOT_FOUND",
            TimeoutError: "TIMEOUT_ERROR",
            PermissionError: "AUTHORIZATION_ERROR"
        }
        
        # Recovery strategies for different error types
        self.recovery_strategies: Dict[str, Callable] = {}
    
    def register_exception_mapping(self, exception_type: Type[Exception], error_code: str):
        """Register a custom exception type to error code mapping"""
        self.exception_mapping[exception_type] = error_code
    
    def register_recovery_strategy(self, error_code: str, strategy: Callable):
        """Register a recovery strategy for a specific error code"""
        self.recovery_strategies[error_code] = strategy
    
    def get_error_code(self, exception: Exception) -> str:
        """Get the error code for an exception"""
        for exc_type, code in self.exception_mapping.items():
            if isinstance(exception, exc_type):
                return code
        return "SERVER_ERROR"
    
    def handle_exception(self, exception: Exception, trace_id: Optional[str] = None) -> ErrorResponse:
        """Handle an exception and return a standardized error response"""
        error_code = self.get_error_code(exception)
        error_message = self.error_codes.get(error_code, "An unexpected error occurred")
        
        # Log the error
        logger.error(f"Error {error_code}: {error_message}")
        logger.error(traceback.format_exc())
        
        # Try to recover if a strategy exists
        if error_code in self.recovery_strategies:
            try:
                self.recovery_strategies[error_code](exception)
                logger.info(f"Recovery strategy for {error_code} executed")
            except Exception as recovery_error:
                logger.error(f"Recovery strategy failed: {recovery_error}")
        
        # Create standardized error response
        return ErrorResponse(
            error=error_message,
            error_code=error_code,
            details={"exception": str(exception)},
            trace_id=trace_id
        )

# Create a singleton instance
error_handler = ErrorHandler()

async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI exception handler that uses the ErrorHandler"""
    trace_id = request.headers.get("X-Trace-ID")
    error_response = error_handler.handle_exception(exc, trace_id)
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPExceptions specifically"""
    trace_id = request.headers.get("X-Trace-ID")
    error_code = "BAD_REQUEST" if exc.status_code == 400 else \
                "AUTHENTICATION_ERROR" if exc.status_code == 401 else \
                "AUTHORIZATION_ERROR" if exc.status_code == 403 else \
                "RESOURCE_NOT_FOUND" if exc.status_code == 404 else \
                "CONFLICT_ERROR" if exc.status_code == 409 else \
                "RATE_LIMIT_ERROR" if exc.status_code == 429 else \
                "SERVER_ERROR"
    
    error_response = ErrorResponse(
        error=exc.detail,
        error_code=error_code,
        trace_id=trace_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers or {},
        content=error_response.dict()
    )

def configure_error_handling(app):
    """Configure FastAPI application with error handlers"""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, exception_handler)