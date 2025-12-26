# Discovery Service - FastAPI Migration

This is a complete migration of the Spring Boot Netflix Eureka Discovery Service to FastAPI with MongoDB.

## Architecture Overview

### Spring Boot to FastAPI Mapping

| Spring Boot | FastAPI |
|-------------|---------|
| `DiscoveryServiceApplication` (main class) | `app/main.py` |
| `@RestController` | `FastAPI` routers in `api/endpoints/` |
| `@Service` | Service classes in `services/` |
| `@Repository` | Repository classes in `repositories/` |
| `@Configuration` / `@Value` | `app/core/config.py` using Pydantic |
| `@Document` (MongoDB) | Pydantic models in `models/aggregates/root/` |
| DTO classes | Pydantic models in `models/DTO/` and `models/response/` |
| Exception handlers (`@ControllerAdvice`) | `exceptions/handlers.py` |
| Spring Data CrudRepository | `repositories/MongoRepository.py` (base async repository) |

## Project Structure

```
discovery-service-fastapi/
├── app/
│   ├── main.py                          # FastAPI app initialization (≈ DiscoveryServiceApplication.java)
│   ├── dependencies.py                  # Dependency injection (≈ Spring @Autowired)
│   ├── api/
│   │   ├── router.py
│   │   └── endpoints/
│   │       └── DiscoveryController.py   # Discovery endpoints (≈ @RestController)
│   ├── core/
│   │   ├── config.py                    # Configuration (≈ @Configuration, @Value)
│   │   ├── constants.py                 # Application constants
│   │   └── ServiceRegistry.py           # (Future: Enhanced service registry)
│   ├── db/
│   │   └── mongodb.py                   # MongoDB async client management
│   ├── models/
│   │   ├── aggregates/root/
│   │   │   └── Service.py               # Domain models (≈ @Document)
│   │   ├── DTO/
│   │   │   ├── InstanceInfo.py          # Instance DTOs
│   │   │   └── ApplicationDTO.py        # Application DTOs
│   │   ├── entity/
│   │   ├── response/
│   │   │   └── ResponseModels.py        # Response DTOs
│   │   └── valueobjects/
│   ├── repositories/
│   │   ├── MongoRepository.py           # Base async repository (≈ CrudRepository)
│   │   ├── ServiceInstanceRepository.py # Instance repository (≈ @Repository)
│   │   └── ServiceRepository.py         # Service repository (≈ @Repository)
│   ├── services/
│   │   └── DiscoveryService.py          # Business logic (≈ @Service)
│   ├── clients/                         # (Future: HTTP clients)
│   ├── security/                        # (Future: JWT, security)
│   ├── exceptions/
│   │   ├── custom_exceptions.py         # Custom exceptions
│   │   └── handlers.py                  # Exception handlers (≈ @ControllerAdvice)
│   └── discovery/                       # (Future: Eureka client)
├── requirements.txt                     # Python dependencies (≈ pom.xml)
├── .env.example                         # Environment variables template
├── Dockerfile                           # Docker image definition
├── docker-compose.yml                   # Docker compose for local development
└── README.md                            # This file
```

## Key Features Implemented

### 1. Service Registration
- **Endpoint**: `POST /eureka/apps/{serviceName}`
- **Equivalent**: Spring's registration endpoint
- **Features**:
  - Register service instances with metadata
  - Validation of required fields
  - Duplicate detection
  - Automatic service creation

### 2. Service Lookup
- **Endpoints**:
  - `GET /eureka/apps` - Get all applications
  - `GET /eureka/apps/{serviceName}` - Get application instances
  - `GET /eureka/apps/instanceId/{instanceId}` - Get specific instance
- **Features**:
  - Fast lookup from MongoDB
  - Separate UP/DOWN instance counts
  - Full metadata retrieval

### 3. Heartbeat/Lease Renewal
- **Endpoint**: `PUT /eureka/apps/{serviceName}/{instanceId}`
- **Features**:
  - Automatic lease expiration detection
  - Lease duration configuration per instance
  - 404 response for expired leases

### 4. Instance Status Management
- **Endpoint**: `PUT /eureka/apps/{serviceName}/{instanceId}/status`
- **Features**:
  - Status updates (UP, DOWN, OUT_OF_SERVICE, STARTING, UNKNOWN)
  - Service metadata updates

### 5. Instance Deregistration
- **Endpoint**: `DELETE /eureka/apps/{serviceName}/{instanceId}`
- **Features**:
  - Clean removal of instances
  - Service cleanup when no instances exist

### 6. Background Tasks
- **Eviction Task**: Runs every 60 seconds
  - Removes expired instances
  - Updates service metadata
  - Equivalent to Eureka's eviction timer

### 7. Health & Info Endpoints
- `/health` - Service health check
- `/eureka/health` - Eureka health endpoint
- `/info` - Application information

## Async/Await Implementation

All database operations use Motor (async MongoDB driver):

```python
# Repository methods are async
async def find_by_instance_id(self, instance_id: str) -> Optional[ServiceInstance]:
    doc = await self.find_one({"instance_id": instance_id})
    if doc:
        return ServiceInstance(**doc)
    return None

# Service methods are async
async def register_instance(self, request: InstanceInfoRequest) -> ServiceInstance:
    # Async operations with await
    existing = await self.instance_repository.find_by_instance_id(request.instance_id)
    ...
    saved = await self.instance_repository.save(instance_dict)
    ...

# Endpoints are async
@router.get("/apps/{app_name}")
async def get_application(app_name: str, discovery_service: DiscoveryService = Depends(get_discovery_service)):
    return await discovery_service.get_application(app_name)
```

## Database Design

### Collections

#### 1. `services`
Stores registered applications/services.

```json
{
  "_id": ObjectId,
  "name": "USER-SERVICE",
  "description": "User Management Service",
  "version": "1.0.0",
  "created_at": ISODate,
  "updated_at": ISODate,
  "instance_count": 3,
  "up_instance_count": 2
}
```

#### 2. `service_instances`
Stores individual service instance registrations.

```json
{
  "_id": ObjectId,
  "instance_id": "user-service-1",
  "app_name": "USER-SERVICE",
  "host_name": "user1.example.com",
  "ip_addr": "192.168.1.101",
  "port": 8081,
  "secure_port": 8443,
  "status": "UP",
  "home_page_url": "http://192.168.1.101:8081/",
  "status_page_url": "http://192.168.1.101:8081/actuator/health",
  "health_check_url": "http://192.168.1.101:8081/actuator/health",
  "metadata": {
    "zone": "us-east-1a",
    "version": "1.0.0"
  },
  "lease_duration_in_secs": 90,
  "lease_renewal_interval_in_secs": 30,
  "registered_at": ISODate,
  "last_heartbeat": ISODate,
  "last_dirty_timestamp": ISODate
}
```

### Indexes

Created on:
- `service_instances.instance_id` (unique)
- `service_instances.app_name`
- `services.name` (unique)

## Configuration

### Environment Variables

See `.env.example`:

```bash
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=discovery_service
SERVER_PORT=8761
SERVER_HOST=0.0.0.0
EUREKA_INSTANCE_HOSTNAME=localhost
LOG_LEVEL=INFO
```

### Application Configuration

Configured in `app/core/config.py` using Pydantic `BaseSettings`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    server_port: int = 8761
    mongodb_url: str = "mongodb://localhost:27017"
    # ... more settings
```

## Error Handling

### Exception Types

- `ServiceNotFound` (404) - Instance/application not found
- `ServiceAlreadyRegistered` (409) - Duplicate instance
- `InvalidServiceData` (400) - Validation failure
- `ApplicationNotFound` (404) - Application not registered
- `DatabaseError` (500) - MongoDB operation failure
- `UnauthorizedRequest` (401) - Authentication failure

### Exception Handlers

Registered in `app/exceptions/handlers.py` with standardized JSON responses:

```json
{
  "status": 404,
  "message": "Service instance not found",
  "timestamp": "2025-01-01T12:00:00Z",
  "path": "/eureka/apps/USER-SERVICE/instance-1"
}
```

## Dependency Injection

Uses FastAPI's `Depends`:

```python
async def get_discovery_service() -> AsyncGenerator[DiscoveryService, None]:
    db = get_database()
    service = DiscoveryService(db)
    yield service

@router.get("/apps")
async def get_all_applications(
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    return await discovery_service.get_all_applications()
```

## Running the Application

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start MongoDB**:
   ```bash
   docker run -d -p 27017:27017 mongo:6.0
   ```

3. **Run the service**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8761 --reload
   ```

4. **Check health**:
   ```bash
   curl http://localhost:8761/health
   ```

### Docker Compose

```bash
docker-compose up -d
```

This starts both MongoDB and the FastAPI service.

### Production

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8761
```

## Testing

### Register an Instance

```bash
curl -X POST http://localhost:8761/eureka/apps/USER-SERVICE \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "user-service-1",
    "app_name": "USER-SERVICE",
    "host_name": "user1.example.com",
    "ip_addr": "192.168.1.101",
    "port": 8081,
    "home_page_url": "http://192.168.1.101:8081/",
    "status_page_url": "http://192.168.1.101:8081/actuator/health",
    "health_check_url": "http://192.168.1.101:8081/actuator/health"
  }'
```

### Get All Applications

```bash
curl http://localhost:8761/eureka/apps
```

### Get Specific Application

```bash
curl http://localhost:8761/eureka/apps/USER-SERVICE
```

### Heartbeat/Lease Renewal

```bash
curl -X PUT http://localhost:8761/eureka/apps/USER-SERVICE/user-service-1
```

### Get Specific Instance

```bash
curl http://localhost:8761/eureka/apps/instanceId/user-service-1
```

### Deregister Instance

```bash
curl -X DELETE http://localhost:8761/eureka/apps/USER-SERVICE/user-service-1
```

## Migration Notes

### Preserved Behavior

✅ All Eureka API endpoints and responses are identical
✅ Same service registration/discovery logic
✅ Lease management and eviction
✅ Instance metadata support
✅ Error handling and HTTP status codes
✅ Background task processing

### Improvements Over Spring Boot

🚀 **Async-First**: All I/O operations are fully asynchronous
🚀 **Motor Driver**: True async MongoDB with connection pooling
🚀 **Type Safety**: Pydantic models with strict validation
🚀 **Lighter Footprint**: FastAPI is more lightweight than Spring Boot
🚀 **Faster Startup**: Significantly faster application startup
🚀 **Better Logging**: Consistent structured logging throughout

### Future Enhancements

- [ ] JWT authentication and authorization
- [ ] Advanced metrics and monitoring
- [ ] Caching layer (Redis)
- [ ] Multi-region federation
- [ ] Rate limiting and request throttling
- [ ] Eureka client library for service discovery
- [ ] GraphQL endpoint option
- [ ] Advanced filtering and query DSL

## Logging

Configured with Python's standard logging:

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Registering instance: {request.instance_id}")
logger.warning(f"Lease expired for instance {instance_id}")
logger.error(f"Database error: {e}")
```

Log level controlled via `LOG_LEVEL` environment variable.

## License

Same as original Spring Boot project.

## Compatibility

**Eureka Clients**: Compatible with standard Eureka clients in all JVM languages.

Example client registration:
```bash
curl -X POST http://localhost:8761/eureka/apps/MY-SERVICE \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "my-service-1",
    "app_name": "MY-SERVICE",
    "host_name": "app1.example.com",
    "ip_addr": "10.0.0.1",
    "port": 8080,
    "home_page_url": "http://10.0.0.1:8080/",
    "status_page_url": "http://10.0.0.1:8080/status",
    "health_check_url": "http://10.0.0.1:8080/health"
  }'
```
