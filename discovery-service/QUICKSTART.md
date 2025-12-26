# Quick Start Guide

## Prerequisites

- Python 3.9+
- MongoDB 5.0+
- Docker & Docker Compose (optional, for containerized deployment)

## Local Development Setup

### 1. Clone & Install Dependencies

```bash
cd discovery-service-fastapi
pip install -r requirements.txt
```

### 2. Start MongoDB

**Option A: Docker**
```bash
docker run -d -p 27017:27017 --name discovery-mongo mongo:6.0
```

**Option B: Docker Compose**
```bash
docker-compose up -d mongodb
```

**Option C: Local Installation**
Ensure MongoDB is running on `localhost:27017`

### 3. Configure Environment (Optional)

Copy `.env.example` to `.env` and customize:
```bash
cp .env.example .env
```

### 4. Run the Service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8761 --reload
```

The service will start at `http://localhost:8761`

### 5. Verify Health

```bash
curl http://localhost:8761/health
```

Response:
```json
{
  "status": "UP",
  "timestamp": "2025-01-01T12:00:00Z",
  "service": "discovery-service"
}
```

---

## Docker Deployment

### Option 1: Build & Run Individual Images

```bash
# Build the image
docker build -t discovery-service:1.0.0 .

# Run with MongoDB
docker run -d \
  -p 27017:27017 \
  --name discovery-mongo \
  mongo:6.0

docker run -d \
  -p 8761:8761 \
  -e MONGODB_URL=mongodb://host.docker.internal:27017 \
  --name discovery-service \
  discovery-service:1.0.0
```

### Option 2: Docker Compose (Recommended)

```bash
docker-compose up -d
```

This starts both MongoDB and the FastAPI service with automatic networking.

### Verify Containerized Deployment

```bash
curl http://localhost:8761/health
```

---

## Basic API Usage

### 1. Register a Service Instance

```bash
curl -X POST http://localhost:8761/eureka/apps/MY-SERVICE \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "my-service-instance-1",
    "app_name": "MY-SERVICE",
    "host_name": "app1.example.com",
    "ip_addr": "10.0.0.1",
    "port": 8080,
    "home_page_url": "http://10.0.0.1:8080/",
    "status_page_url": "http://10.0.0.1:8080/status",
    "health_check_url": "http://10.0.0.1:8080/health",
    "metadata": {
      "zone": "us-east-1a",
      "version": "1.0.0"
    }
  }'
```

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Instance my-service-instance-1 registered successfully",
  "instance_id": "my-service-instance-1",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### 2. Get All Applications

```bash
curl http://localhost:8761/eureka/apps
```

**Response (200 OK)**:
```json
{
  "applications": [
    {
      "app_name": "MY-SERVICE",
      "instance_count": 1,
      "up_instance_count": 1,
      "instances": [
        {
          "instance_id": "my-service-instance-1",
          "app_name": "MY-SERVICE",
          "host_name": "app1.example.com",
          "ip_addr": "10.0.0.1",
          "port": 8080,
          "status": "UP",
          "home_page_url": "http://10.0.0.1:8080/",
          "status_page_url": "http://10.0.0.1:8080/status",
          "health_check_url": "http://10.0.0.1:8080/health",
          "registered_at": "2025-01-01T12:00:00Z",
          "last_heartbeat": "2025-01-01T12:00:00Z"
        }
      ]
    }
  ],
  "total_apps": 1,
  "total_instances": 1,
  "versions_delta": 0
}
```

### 3. Get Specific Application

```bash
curl http://localhost:8761/eureka/apps/MY-SERVICE
```

### 4. Get Specific Instance

```bash
curl http://localhost:8761/eureka/apps/instanceId/my-service-instance-1
```

### 5. Heartbeat / Lease Renewal

Instances should send heartbeats regularly (every 30 seconds recommended):

```bash
curl -X PUT http://localhost:8761/eureka/apps/MY-SERVICE/my-service-instance-1
```

**Response (200 OK)**: Instance with updated `last_heartbeat`

### 6. Update Instance Status

```bash
curl -X PUT "http://localhost:8761/eureka/apps/MY-SERVICE/my-service-instance-1/status?value=DOWN"
```

### 7. Deregister Instance

```bash
curl -X DELETE http://localhost:8761/eureka/apps/MY-SERVICE/my-service-instance-1
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Instance my-service-instance-1 deregistered successfully"
}
```

---

## Error Handling Examples

### 404 - Instance Not Found

```bash
curl http://localhost:8761/eureka/apps/NON-EXISTENT-APP
```

**Response (404 Not Found)**:
```json
{
  "status": 404,
  "message": "Application 'NON-EXISTENT-APP' not found",
  "timestamp": "2025-01-01T12:00:00Z",
  "path": "/eureka/apps/NON-EXISTENT-APP"
}
```

### 400 - Invalid Request

```bash
curl -X POST http://localhost:8761/eureka/apps/MY-SERVICE \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "instance-1"
    # Missing required fields
  }'
```

**Response (400 Bad Request)**:
```json
{
  "status": 400,
  "message": "app_name is required",
  "timestamp": "2025-01-01T12:00:00Z",
  "path": "/eureka/apps/MY-SERVICE"
}
```

### 409 - Duplicate Registration

```bash
curl -X POST http://localhost:8761/eureka/apps/MY-SERVICE \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "existing-instance",
    # ... rest of registration
  }'
```

**Response (409 Conflict)**:
```json
{
  "status": 409,
  "message": "Instance existing-instance is already registered",
  "timestamp": "2025-01-01T12:00:00Z",
  "path": "/eureka/apps/MY-SERVICE"
}
```

---

## Configuration Reference

### Environment Variables

```bash
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=discovery_service

# Server
SERVER_PORT=8761
SERVER_HOST=0.0.0.0

# Eureka
EUREKA_INSTANCE_HOSTNAME=localhost
EUREKA_INSTANCE_PREFER_IP_ADDRESS=true

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Lease Configuration

Default values in `app/core/constants.py`:
- Lease duration: 90 seconds
- Lease renewal interval: 30 seconds
- Eviction task: Every 60 seconds

---

## Development Workflow

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (create tests/test_*.py files)
pytest tests/ -v
```

### Enable Debug Logging

```bash
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

### Database Inspection

```bash
# Connect to MongoDB
mongosh

# Switch database
use discovery_service

# View collections
show collections

# View service instances
db.service_instances.find().pretty()

# View services
db.services.find().pretty()
```

### Monitor Running Service

```bash
# View logs (if running in background)
docker logs discovery-service

# Check health
curl http://localhost:8761/health

# Get service info
curl http://localhost:8761/info
```

---

## Troubleshooting

### MongoDB Connection Failed

**Error**: `Failed to connect to MongoDB`

**Solution**:
1. Verify MongoDB is running: `mongo --version`
2. Check connection string in `.env`
3. Test connection: `mongosh mongodb://localhost:27017`

### Port Already in Use

**Error**: `Address already in use :8761`

**Solution**:
```bash
# Find process using port 8761
lsof -i :8761

# Kill process
kill -9 <PID>

# Or use different port
uvicorn app.main:app --port 8762
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'motor'`

**Solution**:
```bash
pip install -r requirements.txt
```

### Dependency Injection Issues

**Error**: `RuntimeError: Database not initialized`

**Solution**:
- Ensure MongoDB connection succeeds
- Check logs during startup
- Verify lifespan context manager runs

---

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn

gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8761 \
  --access-logfile - \
  --error-logfile -
```

### Docker Production Build

```bash
docker build -t discovery-service:1.0.0 .

docker run -d \
  --name discovery-service \
  -p 8761:8761 \
  -e MONGODB_URL="mongodb://mongo:27017" \
  -e LOG_LEVEL=INFO \
  --restart unless-stopped \
  discovery-service:1.0.0
```

### Kubernetes Deployment

Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: discovery-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: discovery-service
  template:
    metadata:
      labels:
        app: discovery-service
    spec:
      containers:
      - name: discovery-service
        image: discovery-service:1.0.0
        ports:
        - containerPort: 8761
        env:
        - name: MONGODB_URL
          value: "mongodb://mongo:27017"
        - name: LOG_LEVEL
          value: "INFO"
        livenessProbe:
          httpGet:
            path: /health
            port: 8761
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8761
          initialDelaySeconds: 5
          periodSeconds: 10
```

Deploy:
```bash
kubectl apply -f k8s/deployment.yaml
```

---

## Next Steps

1. **Read the full documentation**: See [README.md](README.md)
2. **Understand the migration**: See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
3. **Integrate with your services**: Register instances and perform lookups
4. **Set up monitoring**: Use logging and health endpoints
5. **Customize as needed**: Extend with additional features (JWT, caching, etc.)

---

## Support

For issues or questions:
1. Check logs: `LOG_LEVEL=DEBUG uvicorn app.main:app --reload`
2. Review code comments in service classes
3. Test endpoints manually with curl or Postman
4. Verify MongoDB connectivity and data

Happy service discovering! 🚀
