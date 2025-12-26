"""
Discovery Service Business Logic
Equivalent to Spring @Service class implementing core discovery functionality.
Handles service registration, heartbeat renewal, instance lookup, and eviction.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.aggregates.root.Service import ServiceInstance, Service
from app.models.DTO.InstanceInfo import (
    InstanceInfo,
    InstanceInfoRequest,
    InstanceInfoResponse
)
from app.models.DTO.ApplicationDTO import ApplicationDTO, ApplicationsDTO
from app.models.response.ResponseModels import (
    ApplicationLookupResponse,
    ServiceLookupResponse,
    AllApplicationsResponse
)
from app.repositories.ServiceInstanceRepository import ServiceInstanceRepository
from app.repositories.ServiceRepository import ServiceRepository
from app.exceptions.custom_exceptions import (
    ServiceNotFound,
    ServiceAlreadyRegistered,
    InvalidServiceData,
    ApplicationNotFound
)
from app.core.constants import (
    SERVICE_UP,
    SERVICE_DOWN,
    DEFAULT_LEASE_DURATION_SECONDS,
    DEFAULT_LEASE_RENEWAL_INTERVAL_SECONDS
)

logger = logging.getLogger(__name__)


class DiscoveryService:
    """
    Core discovery service implementing Eureka-like functionality.
    Equivalent to Spring's @Service class with business logic methods.
    
    Responsibilities:
    - Register new service instances
    - Renew instance leases (heartbeat)
    - Deregister service instances
    - Lookup instances by application name
    - Evict expired instances
    - Manage service metadata
    """
    
    def __init__(self, db: Any):
        """
        Initialize with repositories.
        Equivalent to Spring's @Autowired dependency injection.
        
        Args:
            db: Async MongoDB database instance
        """
        self.instance_repository = ServiceInstanceRepository(db)
        self.service_repository = ServiceRepository(db)
        self.db = db
    
    # ==================== Registration Operations ====================
    
    async def register_instance(self, request: InstanceInfoRequest) -> ServiceInstance:
        """
        Register a new service instance.
        Equivalent to Spring's POST /eureka/apps/{serviceName} endpoint logic.
        
        Business Logic:
        1. Validate instance data
        2. Check for duplicates
        3. Create ServiceInstance entity
        4. Save to MongoDB
        5. Update/create Service metadata
        
        Args:
            request: Instance registration request
            
        Returns:
            Registered ServiceInstance
            
        Raises:
            InvalidServiceData: If validation fails
            ServiceAlreadyRegistered: If instance already exists
        """
        logger.info(f"Registering instance: {request.instance_id} for app: {request.app_name}")
        
        # Validate request
        self._validate_instance_request(request)
        
        # Check for duplicates
        existing = await self.instance_repository.find_by_instance_id(request.instance_id)
        if existing:
            raise ServiceAlreadyRegistered(
                f"Instance {request.instance_id} is already registered"
            )
        
        # Create domain model from request
        now = datetime.utcnow()
        
        # Always use server defaults, ignore client-provided values
        # This ensures consistent lease duration across all instances
        lease_duration = DEFAULT_LEASE_DURATION_SECONDS
        lease_renewal_interval = DEFAULT_LEASE_RENEWAL_INTERVAL_SECONDS
        
        service_instance = ServiceInstance(
            instance_id=request.instance_id,
            app_name=request.app_name,
            host_name=request.host_name,
            ip_addr=request.ip_addr,
            port=request.port,
            secure_port=request.secure_port,
            home_page_url=request.home_page_url,
            status_page_url=request.status_page_url,
            health_check_url=request.health_check_url,
            status=request.status or SERVICE_UP,
            metadata=request.metadata or {},
            version_id=request.version_id,
            lease_duration_in_secs=lease_duration,
            lease_renewal_interval_in_secs=lease_renewal_interval,
            registered_at=now,
            last_heartbeat=now,
            last_dirty_timestamp=now,
            lease_expiration_time=now + timedelta(seconds=lease_duration)  # FIX: Calculate properly
        )
        
        # Save to MongoDB
        instance_dict = service_instance.model_dump(exclude={"id"}, by_alias=True)
        saved = await self.instance_repository.save(instance_dict)
        service_instance.id = saved.get("_id")
        
        # Update or create Service metadata
        await self._update_service_metadata(request.app_name)
        
        logger.info(f"Successfully registered instance: {request.instance_id}")
        return service_instance
    
    async def deregister_instance(self, app_name: str, instance_id: str) -> bool:
        """
        Deregister a service instance.
        Equivalent to Spring's DELETE /eureka/apps/{serviceName}/{instanceId}
        
        Business Logic:
        1. Find and delete instance
        2. Update service metadata
        3. Delete service if no instances remain
        
        Args:
            app_name: Application name
            instance_id: Instance identifier
            
        Returns:
            True if successfully deregistered
            
        Raises:
            ServiceNotFound: If instance doesn't exist
        """
        logger.info(f"Deregistering instance {instance_id} for app {app_name}")
        
        # Verify instance exists
        instance = await self.instance_repository.find_by_instance_id(instance_id)
        if not instance or instance.app_name != app_name:
            raise ServiceNotFound(
                f"Instance {instance_id} not found for application {app_name}"
            )
        
        # Delete the instance
        deleted = await self.instance_repository.delete_by_instance_id(instance_id)
        
        if deleted:
            # Update service metadata
            await self._update_service_metadata(app_name)
            logger.info(f"Successfully deregistered instance {instance_id}")
            return True
        
        return False
    
    # ==================== Heartbeat/Lease Renewal ====================
    
    async def renew_lease(self, app_name: str, instance_id: str) -> InstanceInfoResponse:
        """
        Renew the lease for a service instance (heartbeat).
        Equivalent to Spring's PUT /eureka/apps/{serviceName}/{instanceId}
        
        Business Logic:
        1. Find the instance
        2. Check if lease is expired (return 404 if expired)
        3. Update last_heartbeat timestamp
        4. Optionally update status if provided
        
        Args:
            app_name: Application name
            instance_id: Instance identifier
            
        Returns:
            Updated InstanceInfoResponse
            
        Raises:
            ServiceNotFound: If instance not found or lease expired
        """
        logger.info(f"Renewing lease for {instance_id}")
        
        # Find instance
        instance = await self.instance_repository.find_by_instance_id(instance_id)
        if not instance or instance.app_name != app_name:
            raise ServiceNotFound(
                f"Instance {instance_id} not found for application {app_name}"
            )
        
        # Check if lease is expired
        if instance.is_lease_expired():
            logger.warning(f"Lease expired for instance {instance_id}, evicting")
            await self.instance_repository.delete_by_instance_id(instance_id)
            raise ServiceNotFound(
                f"Instance {instance_id} lease has expired"
            )
        
        # Renew lease
        renewed = await self.instance_repository.renew_lease(instance_id)
        if not renewed:
            raise ServiceNotFound(f"Failed to renew lease for {instance_id}")
        
        # Fetch updated instance
        updated = await self.instance_repository.find_by_instance_id(instance_id)
        
        logger.info(f"Successfully renewed lease for {instance_id}")
        return self._convert_to_response(updated)
    
    # ==================== Lookup Operations ====================
    
    async def get_application(self, app_name: str) -> ApplicationLookupResponse:
        """
        Get all instances of a specific application.
        Equivalent to Spring's GET /eureka/apps/{serviceName}
        
        Args:
            app_name: Application name (case-sensitive in Eureka)
            
        Returns:
            ApplicationLookupResponse with all instances
            
        Raises:
            ApplicationNotFound: If application has no registered instances
        """
        logger.info(f"Looking up application: {app_name}")
        
        # Get all instances for the application
        instances = await self.instance_repository.find_by_app_name(app_name)
        if not instances:
            raise ApplicationNotFound(app_name)
        
        # Count UP instances
        up_count = sum(1 for inst in instances if inst.status == SERVICE_UP)
        
        # Convert to response format
        instance_responses = [self._convert_to_response(inst) for inst in instances]
        
        return ApplicationLookupResponse(
            app_name=app_name,
            instance_count=len(instances),
            up_instance_count=up_count,
            instances=instance_responses
        )
    
    async def get_all_applications(self) -> AllApplicationsResponse:
        """
        Get all registered applications and their instances.
        Equivalent to Spring's GET /eureka/apps
        
        Returns:
            AllApplicationsResponse containing all applications
        """
        logger.info("Fetching all applications")
        
        # Get all instances as raw data
        all_docs = await self.instance_repository.find_all()
        
        if not all_docs:
            return AllApplicationsResponse(
                applications=[],
                total_apps=0,
                total_instances=0
            )
        
        # Convert to ServiceInstance objects and group by app_name
        apps_map = {}
        for doc in all_docs:
            instance = ServiceInstance(**doc)
            app_name = instance.app_name
            if app_name not in apps_map:
                apps_map[app_name] = []
            apps_map[app_name].append(instance)
        
        # Create application responses
        applications = []
        total_instances = 0
        
        for app_name, instances in apps_map.items():
            up_count = sum(1 for inst in instances if inst.status == SERVICE_UP)
            instance_responses = [self._convert_to_response(inst) for inst in instances]
            
            app_response = ApplicationLookupResponse(
                app_name=app_name,
                instance_count=len(instances),
                up_instance_count=up_count,
                instances=instance_responses
            )
            applications.append(app_response)
            total_instances += len(instances)
        
        return AllApplicationsResponse(
            applications=applications,
            total_apps=len(applications),
            total_instances=total_instances
        )
    
    async def get_instance(self, instance_id: str) -> InstanceInfoResponse:
        """
        Get a specific instance by ID.
        Equivalent to Spring's GET /eureka/apps/instanceId/{instanceId}
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            InstanceInfoResponse
            
        Raises:
            ServiceNotFound: If instance not found
        """
        instance = await self.instance_repository.find_by_instance_id(instance_id)
        if not instance:
            raise ServiceNotFound(f"Instance {instance_id} not found")
        
        return self._convert_to_response(instance)
    
    # ==================== Status Change Operations ====================
    
    async def update_instance_status(
        self,
        app_name: str,
        instance_id: str,
        status: str
    ) -> bool:
        """
        Update instance status (e.g., from UP to DOWN).
        Equivalent to Spring's PUT /eureka/apps/{serviceName}/{instanceId}/status
        
        Args:
            app_name: Application name
            instance_id: Instance identifier
            status: New status value
            
        Returns:
            True if updated, False if not found
        """
        logger.info(f"Updating status for {instance_id} to {status}")
        
        # Verify instance exists
        instance = await self.instance_repository.find_by_instance_id(instance_id)
        if not instance or instance.app_name != app_name:
            raise ServiceNotFound(f"Instance {instance_id} not found")
        
        updated = await self.instance_repository.update_status(instance_id, status)
        
        if updated:
            # Update service metadata
            await self._update_service_metadata(app_name)
        
        return updated
    
    # ==================== Maintenance Operations ====================
    
    async def evict_expired_instances(self) -> int:
        """
        Evict service instances with expired leases.
        Called periodically by a background task.
        Equivalent to Eureka's eviction timer.
        
        Returns:
            Number of instances evicted
        """
        logger.info("Running eviction task for expired instances")
        
        try:
            # Find all instances
            all_instances = await self.instance_repository.find_all()
            
            evicted_count = 0
            app_names_to_update = set()
            
            for inst_dict in all_instances:
                instance = ServiceInstance(**inst_dict)
                if instance.is_lease_expired():
                    logger.warning(f"Evicting expired instance {instance.instance_id}")
                    await self.instance_repository.delete_by_instance_id(instance.instance_id)
                    evicted_count += 1
                    app_names_to_update.add(instance.app_name)
            
            # Update service metadata for affected applications
            for app_name in app_names_to_update:
                await self._update_service_metadata(app_name)
            
            logger.info(f"Eviction task completed. Evicted {evicted_count} instances")
            return evicted_count
        
        except Exception as e:
            logger.error(f"Error during eviction task: {e}")
            return 0
    
    # ==================== Helper Methods ====================
    
    def _validate_instance_request(self, request: InstanceInfoRequest) -> None:
        """
        Validate instance registration request.
        Equivalent to Spring's validation annotations.
        
        Raises:
            InvalidServiceData: If validation fails
        """
        if not request.instance_id:
            raise InvalidServiceData("instance_id is required")
        if not request.app_name:
            raise InvalidServiceData("app_name is required")
        if not request.host_name:
            raise InvalidServiceData("host_name is required")
        if not request.ip_addr:
            raise InvalidServiceData("ip_addr is required")
        if not request.port or request.port < 1 or request.port > 65535:
            raise InvalidServiceData("port must be a valid port number (1-65535)")
        if not request.home_page_url:
            raise InvalidServiceData("home_page_url is required")
        if not request.status_page_url:
            raise InvalidServiceData("status_page_url is required")
        if not request.health_check_url:
            raise InvalidServiceData("health_check_url is required")
    
    async def _update_service_metadata(self, app_name: str) -> None:
        """
        Update or create service metadata based on current instances.
        Called whenever instances change.
        
        Args:
            app_name: Application name
        """
        try:
            total_count = await self.instance_repository.count_instances_by_app(app_name)
            up_count = await self.instance_repository.count_up_instances_by_app(app_name)
            
            if total_count == 0:
                # Delete service if no instances remain
                await self.service_repository.delete_by_name(app_name)
                logger.info(f"Deleted service {app_name} (no instances)")
            else:
                # Update or create service
                existing = await self.service_repository.find_by_name(app_name)
                
                if existing:
                    await self.service_repository.update_instance_counts(
                        app_name,
                        total_count,
                        up_count
                    )
                else:
                    service = Service(
                        name=app_name,
                        instance_count=total_count,
                        up_instance_count=up_count
                    )
                    service_dict = service.model_dump(exclude={"id"}, by_alias=True)
                    await self.service_repository.save(service_dict)
        
        except Exception as e:
            logger.error(f"Error updating service metadata for {app_name}: {e}")
    
    def _convert_to_response(self, instance: ServiceInstance) -> ServiceLookupResponse:
        """
        Convert ServiceInstance domain model to response DTO.
        
        Args:
            instance: ServiceInstance domain object
            
        Returns:
            ServiceLookupResponse
        """
        return ServiceLookupResponse(
            instance_id=instance.instance_id,
            app_name=instance.app_name,
            host_name=instance.host_name,
            ip_addr=instance.ip_addr,
            port=instance.port,
            secure_port=instance.secure_port,
            status=instance.status,
            home_page_url=instance.home_page_url,
            status_page_url=instance.status_page_url,
            health_check_url=instance.health_check_url,
            metadata=instance.metadata,
            registered_at=instance.registered_at,
            last_heartbeat=instance.last_heartbeat
        )
