"""
Discovery Controller
Equivalent to Spring @RestController for Eureka discovery endpoints
Handles service instance registration, lookup, and management
"""

import logging
from fastapi import APIRouter, Depends, Path, Query, Body, status
from typing import Optional

from app.services.DiscoveryService import DiscoveryService
from app.models.DTO.InstanceInfo import (
    InstanceInfoRequest,
    InstanceInfoResponse
)
from app.models.response.ResponseModels import (
    InstanceRegisterResponse,
    ApplicationLookupResponse,
    AllApplicationsResponse,
    HealthCheckResponse
)
from app.dependencies import get_discovery_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["discovery"])


# ==================== Application Registry Endpoints ====================

@router.get("/apps", response_model=AllApplicationsResponse)
async def get_all_applications(
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Get all registered applications and their instances.
    Equivalent to Spring's GET /eureka/apps
    
    Returns:
        AllApplicationsResponse with all registered applications
    """
    logger.info("GET /eureka/apps - Retrieving all applications")
    return await discovery_service.get_all_applications()


@router.get("/apps/{app_name}", response_model=ApplicationLookupResponse)
async def get_application(
    app_name: str = Path(..., description="Application name"),
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Get all instances of a specific application.
    Equivalent to Spring's GET /eureka/apps/{serviceName}
    
    Args:
        app_name: Name of the application to look up
        
    Returns:
        ApplicationLookupResponse with all instances of the application
    """
    logger.info(f"GET /eureka/apps/{app_name}")
    return await discovery_service.get_application(app_name)


# ==================== Instance Registration Endpoints ====================

@router.post(
    "/apps/{app_name}",
    status_code=status.HTTP_201_CREATED,
    response_model=InstanceRegisterResponse
)
async def register_instance(
    app_name: str = Path(..., description="Application name"),
    instance_request: InstanceInfoRequest = Body(..., description="Instance registration details"),
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Register a new service instance.
    Equivalent to Spring's POST /eureka/apps/{serviceName}
    
    Args:
        app_name: Application name (should match request.app_name)
        instance_request: Instance registration details
        
    Returns:
        InstanceRegisterResponse with registration status
    """
    logger.info(f"POST /eureka/apps/{app_name} - Registering instance")
    
    try:
        # Validate that app_name in URL matches request (case-insensitive)
        if instance_request.app_name.upper() != app_name.upper():
            logger.warning(f"App name mismatch: URL={app_name}, body={instance_request.app_name}")
            return InstanceRegisterResponse(
                success=False,
                message="Application name in URL does not match request body",
                instance_id=None
            )
        
        instance = await discovery_service.register_instance(instance_request)
        
        return InstanceRegisterResponse(
            success=True,
            message=f"Instance {instance.instance_id} registered successfully",
            instance_id=instance.instance_id
        )
    except Exception as e:
        logger.error(f"Error registering instance: {e}", exc_info=True)
        raise


@router.delete(
    "/apps/{app_name}/{instance_id}",
    status_code=status.HTTP_200_OK
)
async def deregister_instance(
    app_name: str = Path(..., description="Application name"),
    instance_id: str = Path(..., description="Instance identifier"),
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Deregister a service instance.
    Equivalent to Spring's DELETE /eureka/apps/{serviceName}/{instanceId}
    
    Args:
        app_name: Application name
        instance_id: Instance identifier
        
    Returns:
        Confirmation of deregistration
    """
    logger.info(f"DELETE /eureka/apps/{app_name}/{instance_id}")
    
    success = await discovery_service.deregister_instance(app_name, instance_id)
    
    return {
        "success": success,
        "message": f"Instance {instance_id} deregistered successfully"
    }


# ==================== Instance Lookup Endpoints ====================

@router.get(
    "/apps/instanceId/{instance_id}",
    response_model=InstanceInfoResponse
)
async def get_instance(
    instance_id: str = Path(..., description="Instance identifier"),
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Get a specific instance by ID.
    Equivalent to Spring's GET /eureka/apps/instanceId/{instanceId}
    
    Args:
        instance_id: Instance identifier
        
    Returns:
        InstanceInfoResponse with instance details
    """
    logger.info(f"GET /eureka/apps/instanceId/{instance_id}")
    return await discovery_service.get_instance(instance_id)


# ==================== Heartbeat/Lease Renewal Endpoints ====================

@router.put(
    "/apps/{app_name}/{instance_id}",
    response_model=InstanceInfoResponse
)
async def renew_lease(
    app_name: str = Path(..., description="Application name"),
    instance_id: str = Path(..., description="Instance identifier"),
    status_param: Optional[str] = Query(None, alias="status", description="Optional status override"),
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Renew the lease for a service instance (heartbeat).
    Equivalent to Spring's PUT /eureka/apps/{serviceName}/{instanceId}
    
    This endpoint should be called periodically by service instances.
    If the request is successful, the instance should continue to renew its lease.
    If a 404 is returned, the instance should re-register.
    
    Args:
        app_name: Application name
        instance_id: Instance identifier
        status_param: Optional status parameter (not used in basic heartbeat)
        
    Returns:
        InstanceInfoResponse with updated instance details
    """
    logger.info(f"PUT /eureka/apps/{app_name}/{instance_id} - Heartbeat renewal")
    
    # If status parameter provided, update instance status
    if status_param:
        await discovery_service.update_instance_status(app_name, instance_id, status_param)
    
    return await discovery_service.renew_lease(app_name, instance_id)


# ==================== Instance Status Update Endpoints ====================

@router.put(
    "/apps/{app_name}/{instance_id}/status",
    status_code=status.HTTP_200_OK
)
async def update_instance_status(
    app_name: str = Path(..., description="Application name"),
    instance_id: str = Path(..., description="Instance identifier"),
    status_value: str = Query(..., alias="value", description="New status value"),
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Update instance status (e.g., from UP to DOWN).
    Equivalent to Spring's PUT /eureka/apps/{serviceName}/{instanceId}/status
    
    Args:
        app_name: Application name
        instance_id: Instance identifier
        status_value: New status value (UP, DOWN, OUT_OF_SERVICE, etc.)
        
    Returns:
        Confirmation of status update
    """
    logger.info(f"PUT /eureka/apps/{app_name}/{instance_id}/status?value={status_value}")
    
    success = await discovery_service.update_instance_status(app_name, instance_id, status_value)
    
    return {
        "success": success,
        "message": f"Instance {instance_id} status updated to {status_value}"
    }


# ==================== Health Check Endpoint ====================

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint for the discovery service.
    Equivalent to Spring Boot Actuator health endpoint.
    
    Returns:
        HealthCheckResponse with service health status
    """
    logger.info("GET /eureka/health - Health check")
    
    return HealthCheckResponse(
        status="UP",
        version="1.0.0"
    )
