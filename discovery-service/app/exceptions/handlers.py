"""
Exception handlers for FastAPI application.
Equivalent to Spring @ControllerAdvice.
Centralized error handling and response formatting.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
from app.exceptions.custom_exceptions import (
    ServiceNotFound,
    ServiceAlreadyRegistered,
    InvalidServiceData,
    ApplicationNotFound,
    DatabaseError,
    UnauthorizedRequest
)

logger = logging.getLogger(__name__)


async def service_not_found_handler(request: Request, exc: ServiceNotFound):
    """Handler for ServiceNotFound exceptions."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "status": status.HTTP_404_NOT_FOUND,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


async def service_already_registered_handler(request: Request, exc: ServiceAlreadyRegistered):
    """Handler for ServiceAlreadyRegistered exceptions."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "status": status.HTTP_409_CONFLICT,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


async def invalid_service_data_handler(request: Request, exc: InvalidServiceData):
    """Handler for InvalidServiceData exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": status.HTTP_400_BAD_REQUEST,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


async def application_not_found_handler(request: Request, exc: ApplicationNotFound):
    """Handler for ApplicationNotFound exceptions."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "status": status.HTTP_404_NOT_FOUND,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


async def database_error_handler(request: Request, exc: DatabaseError):
    """Handler for DatabaseError exceptions."""
    logger.error(f"Database error: {exc.detail}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


async def unauthorized_handler(request: Request, exc: UnauthorizedRequest):
    """Handler for UnauthorizedRequest exceptions."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "status": status.HTTP_401_UNAUTHORIZED,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handler for all unhandled exceptions."""
    logger.error(f"Unhandled exception: {type(exc).__name__} - {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


def register_exception_handlers(app: FastAPI):
    """
    Register all exception handlers with the FastAPI application.
    Called during app initialization.
    """
    app.add_exception_handler(ServiceNotFound, service_not_found_handler)
    app.add_exception_handler(ServiceAlreadyRegistered, service_already_registered_handler)
    app.add_exception_handler(InvalidServiceData, invalid_service_data_handler)
    app.add_exception_handler(ApplicationNotFound, application_not_found_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(UnauthorizedRequest, unauthorized_handler)
    app.add_exception_handler(Exception, general_exception_handler)
