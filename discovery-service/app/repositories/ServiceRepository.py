"""
Service (Application) Repository
Equivalent to Spring Data's @Repository for Service/Application documents.
Provides async operations for managing registered applications.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.repositories.MongoRepository import MongoRepository
from app.models.aggregates.root.Service import Service
from app.core.constants import SERVICES_COLLECTION
from app.exceptions.custom_exceptions import DatabaseError

logger = logging.getLogger(__name__)


class ServiceRepository(MongoRepository[Service]):
    """
    Repository for Service documents.
    Equivalent to Spring Data CrudRepository<Service, String>.
    Manages registered applications and their metadata.
    """
    
    def __init__(self, db: Any):
        """Initialize with Service collection."""
        super().__init__(db, SERVICES_COLLECTION, Service)
    
    async def find_by_name(self, name: str) -> Optional[Service]:
        """
        Find a service by its name.
        Equivalent to Spring's findByName().
        
        Args:
            name: Service/application name
            
        Returns:
            Service object if found, None otherwise
        """
        try:
            doc = await self.find_one({"name": name})
            if doc:
                return Service(**doc)
            return None
        except Exception as e:
            logger.error(f"Error finding service {name}: {e}")
            raise DatabaseError(f"Failed to retrieve service {name}")
    
    async def find_all_services(self) -> List[Service]:
        """
        Find all registered services.
        Equivalent to Spring's findAll().
        
        Returns:
            List of all Service objects
        """
        try:
            docs = await self.find_all()
            return [Service(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error retrieving all services: {e}")
            raise DatabaseError("Failed to retrieve services")
    
    async def exists_by_name(self, name: str) -> bool:
        """
        Check if a service with the given name exists.
        
        Args:
            name: Service name
            
        Returns:
            True if service exists, False otherwise
        """
        try:
            return await self.exists({"name": name})
        except Exception as e:
            logger.error(f"Error checking service existence: {e}")
            raise DatabaseError("Failed to check service existence")
    
    async def update_instance_counts(
        self,
        service_name: str,
        total_instances: int,
        up_instances: int
    ) -> bool:
        """
        Update instance count metadata for a service.
        Called when instances are registered/deregistered.
        
        Args:
            service_name: Service name
            total_instances: Total number of instances
            up_instances: Number of UP instances
            
        Returns:
            True if updated, False if service not found
        """
        try:
            result = await self.collection.update_one(
                {"name": service_name},
                {
                    "$set": {
                        "instance_count": total_instances,
                        "up_instance_count": up_instances,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.matched_count > 0
        except Exception as e:
            logger.error(f"Error updating instance counts for {service_name}: {e}")
            raise DatabaseError(f"Failed to update service metadata")
    
    async def delete_by_name(self, name: str) -> bool:
        """
        Delete a service by name.
        Equivalent to Spring's deleteByName().
        
        Args:
            name: Service name
            
        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.collection.delete_one({"name": name})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting service {name}: {e}")
            raise DatabaseError(f"Failed to delete service {name}")
    
    async def get_service_count(self) -> int:
        """
        Get total count of registered services.
        
        Returns:
            Number of registered services
        """
        try:
            return await self.count({})
        except Exception as e:
            logger.error(f"Error counting services: {e}")
            raise DatabaseError("Failed to count services")
