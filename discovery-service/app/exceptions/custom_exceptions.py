"""
Custom exceptions for the discovery service.
Equivalent to custom Spring exceptions.
"""

from fastapi import HTTPException, status


class ServiceNotFound(HTTPException):
    """
    Exception thrown when a service instance is not found.
    Equivalent to @NotFoundException in Spring.
    """
    
    def __init__(self, detail: str = "Service instance not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ServiceAlreadyRegistered(HTTPException):
    """
    Exception thrown when attempting to register a service that already exists.
    """
    
    def __init__(self, detail: str = "Service instance already registered"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InvalidServiceData(HTTPException):
    """
    Exception thrown when service registration data is invalid.
    Equivalent to @BadRequestException in Spring.
    """
    
    def __init__(self, detail: str = "Invalid service instance data"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ApplicationNotFound(HTTPException):
    """
    Exception thrown when an application is not found.
    """
    
    def __init__(self, app_name: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{app_name}' not found"
        )


class DatabaseError(HTTPException):
    """
    Exception thrown when database operations fail.
    Equivalent to DataAccessException in Spring Data.
    """
    
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class UnauthorizedRequest(HTTPException):
    """
    Exception thrown for unauthorized requests.
    """
    
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
