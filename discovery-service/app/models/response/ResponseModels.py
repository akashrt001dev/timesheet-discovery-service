"""
Response models for API endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ErrorResponse(BaseModel):
    """
    Standard error response format.
    Equivalent to Spring Boot error responses.
    """
    
    status: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """
    Health check response.
    Equivalent to Spring Boot Actuator health endpoint.
    """
    
    status: str = Field(default="UP", description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    services_registered: int = Field(default=0)
    instances_registered: int = Field(default=0)


class InstanceRegisterResponse(BaseModel):
    """
    Response after instance registration.
    """
    
    success: bool
    message: str
    instance_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ServiceLookupResponse(BaseModel):
    """
    Response for service instance lookup.
    """
    
    instance_id: str
    app_name: str
    host_name: str
    ip_addr: str
    port: int
    secure_port: Optional[int] = None
    status: str
    home_page_url: str
    status_page_url: str
    health_check_url: str
    metadata: Dict[str, str] = Field(default_factory=dict)
    registered_at: datetime
    last_heartbeat: datetime


class ApplicationLookupResponse(BaseModel):
    """
    Response containing all instances of an application.
    """
    
    app_name: str
    instance_count: int
    up_instance_count: int
    instances: List[ServiceLookupResponse] = Field(default_factory=list)


class AllApplicationsResponse(BaseModel):
    """
    Response containing all registered applications and instances.
    Equivalent to Netflix Eureka's /eureka/apps response.
    """
    
    applications: List[ApplicationLookupResponse] = Field(default_factory=list)
    total_apps: int = Field(default=0)
    total_instances: int = Field(default=0)
    versions_delta: int = Field(default=0)
