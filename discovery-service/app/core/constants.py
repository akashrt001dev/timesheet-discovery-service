"""
Application Constants
Centralized constants used throughout the application
"""

# Status codes for service instances
SERVICE_UP = "UP"
SERVICE_DOWN = "DOWN"
SERVICE_OUT_OF_SERVICE = "OUT_OF_SERVICE"
SERVICE_STARTING = "STARTING"
SERVICE_UNKNOWN = "UNKNOWN"

# Default values
DEFAULT_LEASE_DURATION_SECONDS = 120  # 2 minutes (for testing)
DEFAULT_LEASE_RENEWAL_INTERVAL_SECONDS = 40  # ~40 seconds (for testing)
DEFAULT_INITIAL_LEASE_DURATION_SECONDS = 120  # 2 minutes (for testing)

# Error messages
ERROR_SERVICE_NOT_FOUND = "Service instance not found"
ERROR_SERVICE_ALREADY_REGISTERED = "Service instance already registered"
ERROR_INVALID_SERVICE_DATA = "Invalid service instance data"
ERROR_INVALID_EUREKA_METADATA = "Invalid Eureka metadata"
ERROR_INTERNAL_SERVER_ERROR = "Internal server error"

# API constants
EUREKA_API_PREFIX = "/eureka"
DISCOVERY_API_PREFIX = "/discovery"
REGISTRATION_API_PREFIX = "/registration"

# Collection names (MongoDB)
SERVICES_COLLECTION = "services"
SERVICE_INSTANCES_COLLECTION = "service_instances"
