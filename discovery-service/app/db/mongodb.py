"""
MongoDB Connection Management
Equivalent to Spring Data MongoDB auto-configuration
Handles async Motor client initialization and lifecycle
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Any
from contextlib import asynccontextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global client reference
_mongodb_client: Optional[Any] = None
_database: Optional[Any] = None


async def connect_to_mongo():
    """
    Initialize MongoDB async client and connect.
    Called on application startup.
    """
    global _mongodb_client, _database
    
    logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
    
    _mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
    _database = _mongodb_client[settings.mongodb_database]
    
    # Test connection
    try:
        await _mongodb_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """
    Close MongoDB async client connection.
    Called on application shutdown.
    """
    global _mongodb_client, _database
    
    if _mongodb_client:
        logger.info("Closing MongoDB connection")
        _mongodb_client.close()
        _mongodb_client = None
        _database = None


def get_database() -> Any:
    """
    Retrieve the async MongoDB database instance.
    Used for dependency injection in repositories.
    """
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return _database


@asynccontextmanager
async def get_mongo_client():
    """
    Context manager for MongoDB client access.
    Ensures proper connection handling.
    """
    if _mongodb_client is None:
        raise RuntimeError("MongoDB client not initialized. Call connect_to_mongo() first.")
    try:
        yield _mongodb_client
    except Exception as e:
        logger.error(f"MongoDB client error: {e}")
        raise
