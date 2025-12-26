"""
Service Instance Repository
Equivalent to Spring Data's @Repository interface and ServiceInstanceRepository.
Provides specialized async operations for ServiceInstance documents.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.repositories.MongoRepository import MongoRepository
from app.models.aggregates.root.Service import ServiceInstance
from app.core.constants import SERVICE_INSTANCES_COLLECTION
from app.exceptions.custom_exceptions import DatabaseError, ServiceNotFound

logger = logging.getLogger(__name__)


class ServiceInstanceRepository(MongoRepository[ServiceInstance]):
    """
    Repository for ServiceInstance documents.
    Equivalent to Spring Data CrudRepository<ServiceInstance, String>.
    Provides custom async finder methods specific to service discovery.
    """
    
    def __init__(self, db: Any):
        """Initialize with ServiceInstance collection."""
        super().__init__(db, SERVICE_INSTANCES_COLLECTION, ServiceInstance)
    
    async def find_by_instance_id(self, instance_id: str) -> Optional[ServiceInstance]:
        """
        Find a service instance by instance ID.
        Equivalent to Spring's findByInstanceId().
        
        Args:
            instance_id: The instance identifier
            
        Returns:
            ServiceInstance if found, None otherwise
        """
        try:
            doc = await self.find_one({"instance_id": instance_id})
            if doc:
                return ServiceInstance(**doc)
            return None
        except Exception as e:
            logger.error(f"Error finding instance {instance_id}: {e}")
            raise DatabaseError(f"Failed to retrieve instance {instance_id}")
    
    async def find_by_app_name(self, app_name: str) -> List[ServiceInstance]:
        """
        Find all instances of a particular application.
        Equivalent to Spring's findByAppName().
        
        Args:
            app_name: Application name
            
        Returns:
            List of ServiceInstance objects for the application
        """
        try:
            docs = await self.find_by_query({"app_name": app_name})
            return [ServiceInstance(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error finding instances for app {app_name}: {e}")
            raise DatabaseError(f"Failed to retrieve instances for app {app_name}")
    
    async def find_up_instances_by_app(self, app_name: str) -> List[ServiceInstance]:
        """
        Find all UP instances of an application.
        Equivalent to Spring's findUpInstancesByApp() or similar.
        
        Args:
            app_name: Application name
            
        Returns:
            List of UP ServiceInstance objects
        """
        try:
            docs = await self.find_by_query({
                "app_name": app_name,
                "status": "UP"
            })
            return [ServiceInstance(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error finding UP instances for app {app_name}: {e}")
            raise DatabaseError(f"Failed to retrieve UP instances for app {app_name}")
    
    async def find_expired_leases(self) -> List[ServiceInstance]:
        """
        Find all service instances with expired leases.
        Used for eviction of stale registrations.
        
        Returns:
            List of ServiceInstance objects with expired leases
        """
        try:
            current_time = datetime.utcnow()
            docs = await self.collection.find({
                "$expr": {
                    "$gt": [
                        {"$add": ["$last_heartbeat", {"$multiply": ["$lease_duration_in_secs", 1000]}]},
                        current_time
                    ]
                }
            }).to_list(length=None)
            return [ServiceInstance(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error finding expired leases: {e}")
            raise DatabaseError("Failed to retrieve expired leases")
    
    async def update_status(self, instance_id: str, status: str) -> bool:
        """
        Update the status of a service instance.
        
        Args:
            instance_id: Instance identifier
            status: New status (UP, DOWN, OUT_OF_SERVICE, etc.)
            
        Returns:
            True if updated, False if not found
        """
        try:
            result = await self.collection.update_one(
                {"instance_id": instance_id},
                {
                    "$set": {
                        "status": status,
                        "last_dirty_timestamp": datetime.utcnow()
                    }
                }
            )
            return result.matched_count > 0
        except Exception as e:
            logger.error(f"Error updating status for {instance_id}: {e}")
            raise DatabaseError(f"Failed to update instance status")
    
    async def renew_lease(self, instance_id: str) -> bool:
        """
        Renew the lease for a service instance (heartbeat).
        Equivalent to Spring's renew() method.
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            True if renewed, False if instance not found
        """
        try:
            result = await self.collection.update_one(
                {"instance_id": instance_id},
                {
                    "$set": {
                        "last_heartbeat": datetime.utcnow(),
                        "last_dirty_timestamp": datetime.utcnow()
                    }
                }
            )
            return result.matched_count > 0
        except Exception as e:
            logger.error(f"Error renewing lease for {instance_id}: {e}")
            raise DatabaseError(f"Failed to renew lease for instance")
    
    async def delete_by_instance_id(self, instance_id: str) -> bool:
        """
        Delete a service instance by instance ID.
        Equivalent to Spring's deleteByInstanceId().
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.collection.delete_one({"instance_id": instance_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting instance {instance_id}: {e}")
            raise DatabaseError(f"Failed to delete instance {instance_id}")
    
    async def delete_expired_instances(self) -> int:
        """
        Delete all service instances with expired leases.
        Used as part of the eviction process.
        
        Returns:
            Number of instances deleted
        """
        try:
            current_time = datetime.utcnow()
            expired_instances = await self.find_expired_leases()
            
            count = 0
            for instance in expired_instances:
                if instance.is_lease_expired():
                    await self.delete_by_instance_id(instance.instance_id)
                    count += 1
            
            logger.info(f"Deleted {count} expired service instances")
            return count
        except Exception as e:
            logger.error(f"Error deleting expired instances: {e}")
            raise DatabaseError("Failed to delete expired instances")
    
    async def count_instances_by_app(self, app_name: str) -> int:
        """
        Count the number of instances for an application.
        
        Args:
            app_name: Application name
            
        Returns:
            Number of instances
        """
        try:
            return await self.count({"app_name": app_name})
        except Exception as e:
            logger.error(f"Error counting instances for app {app_name}: {e}")
            raise DatabaseError(f"Failed to count instances for app {app_name}")
    
    async def count_up_instances_by_app(self, app_name: str) -> int:
        """
        Count the number of UP instances for an application.
        
        Args:
            app_name: Application name
            
        Returns:
            Number of UP instances
        """
        try:
            return await self.count({"app_name": app_name, "status": "UP"})
        except Exception as e:
            logger.error(f"Error counting UP instances for app {app_name}: {e}")
            raise DatabaseError(f"Failed to count UP instances for app {app_name}")
