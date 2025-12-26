"""
ServiceInstance Aggregate Root
Equivalent to Spring Data MongoDB @Document
Represents the domain model for service instances stored in MongoDB
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime
from bson import ObjectId


class ServiceInstance(BaseModel):
    """
    Service instance aggregate root.
    Equivalent to @Document class in Spring Data MongoDB
    Represents a single instance of a registered service.
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True, from_attributes=True)
    
    # MongoDB document ID
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    
    # Instance identification
    instance_id: str = Field(..., index=True, description="Unique instance identifier")
    app_name: str = Field(..., index=True, description="Application/service name")
    
    # Network information
    host_name: str
    ip_addr: str
    port: int
    secure_port: Optional[int] = None
    
    # URLs
    home_page_url: str
    status_page_url: str
    health_check_url: str
    
    # Service status
    status: str = Field(default="UP", description="UP|DOWN|OUT_OF_SERVICE|STARTING|UNKNOWN")
    
    # Zone awareness for load balancing
    zone: Optional[str] = Field(None, description="Availability zone")
    region: Optional[str] = Field(None, description="Cloud region")
    
    # Lease information
    lease_duration_in_secs: int = Field(default=90, description="Lease duration in seconds")
    lease_renewal_interval_in_secs: int = Field(default=30, description="Heartbeat renewal interval in seconds")
    lease_expiration_time: datetime = Field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    
    # Timestamps
    registration_time: datetime = Field(default_factory=datetime.utcnow)
    last_renewal_time: datetime = Field(default_factory=datetime.utcnow)
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    last_dirty_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)
    version_id: Optional[str] = Field(default=None, description="Version identifier")
    
    def is_lease_expired(self) -> bool:
        """
        Check if the lease for this instance has expired.
        Returns True if current time is beyond lease expiration time.
        
        Returns:
            bool: True if lease is expired, False otherwise
        """
        return datetime.utcnow() > self.lease_expiration_time
    
    def calculate_lease_expiration(self) -> datetime:
        """
        Calculate the lease expiration time based on last heartbeat and lease duration.
        
        Returns:
            datetime: The calculated lease expiration time
        """
        from datetime import timedelta
        return self.last_heartbeat + timedelta(seconds=self.lease_duration_in_secs)


class Service(BaseModel):
    """
    Application/Service aggregate root.
    Groups all instances of a particular service.
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True, from_attributes=True)
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    
    # Service identification
    name: str = Field(..., index=True, unique=True, description="Service/application name")
    
    # Service metadata
    description: Optional[str] = None
    version: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Instance count tracking
    instance_count: int = Field(default=0)
    up_instance_count: int = Field(default=0)
