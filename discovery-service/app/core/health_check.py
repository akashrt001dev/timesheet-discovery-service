"""
Health Check Manager with Resilience
Handles health checks for service instances with retry logic
"""

import logging
import asyncio
from typing import Optional
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)


class HealthCheckConfig:
    """Configuration for health checks"""
    
    def __init__(
        self,
        max_retries: int = 3,
        timeout_seconds: int = 5,
        backoff_factor: float = 2.0,
        initial_delay_seconds: float = 1.0
    ):
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.backoff_factor = backoff_factor
        self.initial_delay_seconds = initial_delay_seconds


class HealthCheckManager:
    """Manages health checks with exponential backoff retry"""
    
    def __init__(self, config: Optional[HealthCheckConfig] = None):
        self.config = config or HealthCheckConfig()
        self.client = httpx.AsyncClient(timeout=self.config.timeout_seconds)
        self.last_check_results = {}  # Track last check time per instance
    
    async def check_health(self, health_check_url: str, instance_id: str) -> bool:
        """
        Check health of an instance with retry logic
        
        Args:
            health_check_url: URL to check health
            instance_id: Instance identifier for logging
            
        Returns:
            True if health check passes, False otherwise
        """
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.get(health_check_url)
                
                if response.status_code == 200:
                    logger.debug(f"Health check passed for {instance_id}")
                    self.last_check_results[instance_id] = {
                        'status': 'UP',
                        'timestamp': datetime.utcnow(),
                        'attempts': attempt + 1
                    }
                    return True
                
            except asyncio.TimeoutError:
                logger.warning(
                    f"Health check timeout for {instance_id} "
                    f"(attempt {attempt + 1}/{self.config.max_retries})"
                )
            except httpx.HTTPError as e:
                logger.warning(
                    f"Health check failed for {instance_id}: {str(e)} "
                    f"(attempt {attempt + 1}/{self.config.max_retries})"
                )
            except Exception as e:
                logger.error(f"Unexpected error during health check for {instance_id}: {e}")
            
            # Exponential backoff before retry
            if attempt < self.config.max_retries - 1:
                delay = self.config.initial_delay_seconds * (
                    self.config.backoff_factor ** attempt
                )
                logger.debug(f"Retrying health check in {delay}s for {instance_id}")
                await asyncio.sleep(delay)
        
        logger.error(f"Health check failed for {instance_id} after {self.config.max_retries} attempts")
        self.last_check_results[instance_id] = {
            'status': 'DOWN',
            'timestamp': datetime.utcnow(),
            'attempts': self.config.max_retries
        }
        return False
    
    async def check_health_batch(
        self,
        instances: list,
        field_name: str = 'health_check_url',
        id_field: str = 'instance_id'
    ) -> dict:
        """
        Check health of multiple instances concurrently
        
        Args:
            instances: List of instance dictionaries
            field_name: Field name containing health check URL
            id_field: Field name containing instance ID
            
        Returns:
            Dictionary with instance_id as key and health status as value
        """
        tasks = [
            self.check_health(
                inst.get(field_name),
                inst.get(id_field)
            )
            for inst in instances
            if inst.get(field_name)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            inst.get(id_field): result
            for inst, result in zip(instances, results)
            if not isinstance(result, Exception)
        }
    
    def get_last_check_result(self, instance_id: str) -> Optional[dict]:
        """Get last health check result for instance"""
        return self.last_check_results.get(instance_id)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global health check manager
_health_check_manager: Optional[HealthCheckManager] = None


def get_health_check_manager() -> HealthCheckManager:
    """Get or create global health check manager"""
    global _health_check_manager
    if _health_check_manager is None:
        _health_check_manager = HealthCheckManager()
    return _health_check_manager
