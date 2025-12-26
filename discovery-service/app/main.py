"""
Main FastAPI Application
Equivalent to Spring Boot DiscoveryServiceApplication class
Initializes the FastAPI application, configures routes, and manages lifecycle
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.constants import EUREKA_API_PREFIX
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.exceptions.handlers import register_exception_handlers
from app.api.endpoints.DiscoveryController import router as discovery_router
from app.services.DiscoveryService import DiscoveryService
from app.db.mongodb import get_database
from app.core.health_check import get_health_check_manager
from app.core.self_preservation import get_self_preservation_mode

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ==================== Background Tasks ====================

async def eviction_task(app: FastAPI):
    """
    Background task to evict expired service instances.
    Equivalent to Eureka's eviction timer.
    Runs periodically to clean up stale registrations.
    """
    await asyncio.sleep(60)  # Wait 60 seconds before starting
    
    while True:
        try:
            logger.info("Starting eviction task")
            db = get_database()
            discovery_service = DiscoveryService(db)
            await discovery_service.evict_expired_instances()
            
            # Run eviction every 60 seconds (configurable)
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Error in eviction task: {e}")
            await asyncio.sleep(60)


# ==================== Lifespan Context Manager ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Equivalent to Spring's @PostConstruct and @PreDestroy annotations.
    
    Handles:
    - Application startup: Connect to MongoDB, start background tasks
    - Application shutdown: Close MongoDB connection, stop background tasks
    """
    
    # ==================== Startup ====================
    logger.info("=" * 80)
    logger.info("Starting Discovery Service")
    logger.info(f"Service Name: {settings.application_name}")
    logger.info(f"Service Version: {settings.application_version}")
    logger.info(f"Server: {settings.server_host}:{settings.server_port}")
    logger.info(f"MongoDB URL: {settings.mongodb_url}")
    logger.info("=" * 80)
    
    # Connect to MongoDB
    await connect_to_mongo()
    logger.info("MongoDB connection established")
    
    # Start background eviction task
    eviction_task_handle = asyncio.create_task(eviction_task(app))
    logger.info("Eviction task started")
    
    yield
    
    # ==================== Shutdown ====================
    logger.info("=" * 80)
    logger.info("Shutting down Discovery Service")
    logger.info("=" * 80)
    
    # Cancel eviction task
    eviction_task_handle.cancel()
    try:
        await eviction_task_handle
    except asyncio.CancelledError:
        logger.info("Eviction task cancelled")
    
    # Close MongoDB connection
    await close_mongo_connection()
    logger.info("MongoDB connection closed")


# ==================== Application Initialization ====================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    Equivalent to Spring Boot @SpringBootApplication initialization.
    
    Returns:
        Configured FastAPI application instance
    """
    
    app = FastAPI(
        title=settings.application_name,
        description="Netflix Eureka Service Discovery Server - FastAPI Implementation",
        version=settings.application_version,
        lifespan=lifespan
    )
    
    # ==================== Exception Handlers ====================
    register_exception_handlers(app)
    
    # ==================== Routes ====================
    app.include_router(discovery_router, prefix=EUREKA_API_PREFIX)
    
    # ==================== Metrics Endpoint ====================
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # ==================== Health Endpoint ====================
    @app.get("/health")
    async def root_health():
        """Root health check endpoint with self-preservation status."""
        spm = get_self_preservation_mode()
        return {
            "status": "UP",
            "timestamp": datetime.utcnow().isoformat(),
            "service": settings.application_name,
            "self_preservation_mode": spm.get_status()
        }
    
    # ==================== Info Endpoint (Actuator equivalent) ====================
    @app.get("/info")
    async def info():
        """Application info endpoint equivalent to Spring Actuator."""
        return {
            "name": settings.application_name,
            "version": settings.application_version,
            "description": "Netflix Eureka Service Discovery Server",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # ==================== Self-Preservation Status Endpoint ====================
    @app.get("/self-preservation")
    async def self_preservation_status():
        """Get self-preservation mode status."""
        spm = get_self_preservation_mode()
        return spm.get_status()
    
    logger.info("FastAPI application configured successfully")
    logger.info("Prometheus metrics available at /metrics")
    return app


# Create the application instance
app = create_app()
