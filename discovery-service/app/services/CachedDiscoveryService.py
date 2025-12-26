"""
Enhanced Discovery Service with Caching and Metrics
Extends the base DiscoveryService with performance optimizations
"""

import logging
from typing import Optional, Any
from app.services.DiscoveryService import DiscoveryService
from app.models.response.ResponseModels import (
    ApplicationLookupResponse,
    AllApplicationsResponse
)
from app.core.caching import get_cache
from app.core.metrics import MetricsTracker

logger = logging.getLogger(__name__)


class CachedDiscoveryService(DiscoveryService):
    """
    Enhanced Discovery Service with caching layer
    Caches application lookups to improve performance for read-heavy workloads
    """
    
    CACHE_TTL_SECONDS = 30  # Cache lookup results for 30 seconds
    
    def __init__(self, db: Any):
        super().__init__(db)
        self.cache = get_cache()
    
    async def get_application(self, app_name: str) -> ApplicationLookupResponse:
        """
        Get all instances of a specific application with caching.
        
        Args:
            app_name: Application name
            
        Returns:
            ApplicationLookupResponse with all instances
        """
        cache_key = f"app:{app_name}"
        
        # Try to get from cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for application: {app_name}")
            return cached_result
        
        logger.debug(f"Cache miss for application: {app_name}")
        
        # Get from database
        with MetricsTracker.track_lookup("application"):
            result = await super().get_application(app_name)
        
        # Cache the result
        await self.cache.set(cache_key, result, self.CACHE_TTL_SECONDS)
        
        return result
    
    async def get_all_applications(self) -> AllApplicationsResponse:
        """
        Get all registered applications and their instances with caching.
        
        Returns:
            AllApplicationsResponse containing all applications
        """
        cache_key = "all_applications"
        
        # Try to get from cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug("Cache hit for all applications")
            return cached_result
        
        logger.debug("Cache miss for all applications")
        
        # Get from database
        with MetricsTracker.track_lookup("all_applications"):
            result = await super().get_all_applications()
        
        # Cache the result
        await self.cache.set(cache_key, result, self.CACHE_TTL_SECONDS)
        
        return result
    
    async def invalidate_application_cache(self, app_name: Optional[str] = None):
        """
        Invalidate cache entries when instances are registered/deregistered
        
        Args:
            app_name: Application name to invalidate. If None, invalidates all
        """
        if app_name:
            await self.cache.invalidate(f"app:{app_name}")
            logger.debug(f"Invalidated cache for application: {app_name}")
        else:
            await self.cache.invalidate_pattern("app:")
            await self.cache.invalidate("all_applications")
            logger.debug("Invalidated all application caches")
    
    async def register_instance(self, request):
        """
        Register instance and invalidate cache
        """
        result = await super().register_instance(request)
        await self.invalidate_application_cache(request.app_name)
        return result
    
    async def deregister_instance(self, app_name: str, instance_id: str) -> bool:
        """
        Deregister instance and invalidate cache
        """
        result = await super().deregister_instance(app_name, instance_id)
        await self.invalidate_application_cache(app_name)
        return result
    
    async def renew_lease(self, app_name: str, instance_id: str):
        """
        Renew lease (heartbeat) without cache invalidation
        Heartbeats don't change application state, so no cache invalidation needed
        """
        return await super().renew_lease(app_name, instance_id)
