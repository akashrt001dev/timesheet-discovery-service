"""
Application Data Transfer Object
Represents a registered application (service) with its instances
Equivalent to Netflix Eureka's Application class
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ApplicationDTO(BaseModel):
    """
    Application metadata with all registered instances.
    Equivalent to com.netflix.eureka.model.Application
    """
    
    name: str = Field(..., description="Application name")
    instances: List[dict] = Field(default_factory=list, description="List of instance metadata")
    updated_timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "USER-SERVICE",
                "instances": [
                    {
                        "instance_id": "user-service-1",
                        "host_name": "user.example.com",
                        "ip_addr": "192.168.1.101",
                        "port": 8081,
                        "status": "UP"
                    }
                ],
                "updated_timestamp": "2025-01-01T00:00:00Z"
            }
        }


class ApplicationsDTO(BaseModel):
    """
    Container for all registered applications.
    Equivalent to Netflix Eureka's Applications response.
    """
    
    applications: List[ApplicationDTO] = Field(default_factory=list)
    versions_delta: int = Field(default=0)
    apps_hash_code: str = Field(default="")
    
    class Config:
        json_schema_extra = {
            "example": {
                "applications": [
                    {
                        "name": "USER-SERVICE",
                        "instances": []
                    }
                ],
                "versions_delta": 1,
                "apps_hash_code": "abcdef123456"
            }
        }
