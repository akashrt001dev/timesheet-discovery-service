"""
FastAPI Dependency Injection Module
Equivalent to Spring's @Autowired and @Bean annotations
Provides dependency resolution for services, repositories, and utilities
"""

from typing import AsyncGenerator, Any

from app.db.mongodb import get_database
from app.services.CachedDiscoveryService import CachedDiscoveryService


async def get_discovery_service() -> AsyncGenerator[CachedDiscoveryService, None]:
    """
    Dependency injection for CachedDiscoveryService.
    Equivalent to Spring's @Autowired on DiscoveryService.
    Uses the cached version for improved performance on lookups.
    
    Yields:
        CachedDiscoveryService instance with injected dependencies
    """
    db: Any = get_database()
    service = CachedDiscoveryService(db)
    yield service
