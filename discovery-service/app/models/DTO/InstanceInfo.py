"""
InstanceInfo Data Transfer Object
Equivalent to Netflix Eureka's InstanceInfo class
Represents registration/lookup information for service instances
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class InstanceInfo(BaseModel):
    """
    Instance metadata and registration information.
    Equivalent to com.netflix.eureka.model.InstanceInfo
    """
    
    instance_id: str = Field(..., description="Unique instance identifier")
    host_name: str = Field(..., description="Hostname of the instance")
    app_name: str = Field(..., description="Application name (service name)")
    ip_addr: str = Field(..., description="IP address of the instance")
    status: str = Field(default="UP", description="Service status (UP/DOWN/OUT_OF_SERVICE)")
    port: int = Field(..., description="Port number where service is running")
    secure_port: Optional[int] = Field(None, description="HTTPS port if applicable")
    home_page_url: str = Field(..., description="Home page URL of the instance")
    status_page_url: str = Field(..., description="Status page URL")
    health_check_url: str = Field(..., description="Health check URL")
    version_id: Optional[str] = Field(None, description="Version of the instance")
    
    # Zone awareness for load balancing
    zone: Optional[str] = Field(None, description="Availability zone (e.g., us-east-1a, us-west-2b)")
    region: Optional[str] = Field(None, description="Cloud region (e.g., us-east-1, us-west-2)")
    
    # Eureka metadata
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict, description="Custom metadata")
    lease_duration_in_secs: int = Field(default=90, description="Lease duration in seconds")
    lease_renewal_interval_in_secs: int = Field(default=30, description="Lease renewal interval")
    
    # Timestamps
    registered_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_heartbeat: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_dirty_timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "instance_id": "app-instance-1",
                "host_name": "app.example.com",
                "app_name": "APP-SERVICE",
                "ip_addr": "192.168.1.100",
                "port": 8080,
                "secure_port": 8443,
                "status": "UP",
                "home_page_url": "http://192.168.1.100:8080/",
                "status_page_url": "http://192.168.1.100:8080/status",
                "health_check_url": "http://192.168.1.100:8080/health",
                "zone": "us-east-1a",
                "region": "us-east-1"
            }
        }


class InstanceInfoRequest(BaseModel):
    """
    Request DTO for instance registration/update.
    Equivalent to registration request payload.
    """
    
    instance_id: str
    host_name: str
    app_name: str
    ip_addr: str
    port: int
    secure_port: Optional[int] = None
    home_page_url: str
    status_page_url: str
    health_check_url: str
    status: Optional[str] = "UP"
    zone: Optional[str] = None
    region: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    version_id: Optional[str] = None
    lease_duration_in_secs: Optional[int] = 90
    lease_renewal_interval_in_secs: Optional[int] = 30


class InstanceInfoResponse(BaseModel):
    """
    Response DTO for instance queries.
    """
    
    instance_id: str
    host_name: str
    app_name: str
    ip_addr: str
    port: int
    secure_port: Optional[int] = None
    status: str
    home_page_url: str
    status_page_url: str
    health_check_url: str
    zone: Optional[str] = None
    region: Optional[str] = None
    registered_at: datetime
    last_heartbeat: datetime
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
