# Enhanced Eureka Discovery Service - Deployment Guide

## Pre-Deployment Checklist

- [ ] Python 3.8+ installed
- [ ] MongoDB running and accessible
- [ ] `.env` file configured with correct MongoDB URL
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Port 8761 available for the service
- [ ] Port 9090 available for Prometheus (if using)

## Installation & Deployment

### 1. Install Dependencies

```bash
# Navigate to project directory
cd discovery-service-fastapi

# Install all dependencies including new ones
pip install -r requirements.txt
```

### 2. Configuration

Review and update `.env` file:

```env
# MongoDB Configuration
MONGODB_URL=mongodb://user:password@host:port/database
MONGODB_DATABASE=your_database

# Server Configuration
SERVER_PORT=8761
SERVER_HOST=0.0.0.0

# Eureka Configuration
EUREKA_INSTANCE_HOSTNAME=localhost
EUREKA_INSTANCE_PREFER_IP_ADDRESS=true
EUREKA_CLIENT_REGISTER_WITH_EUREKA=false
EUREKA_CLIENT_FETCH_REGISTRY=false

# Logging
LOG_LEVEL=INFO
```

### 3. Start the Service

#### Option A: Using the Shell Script (Linux/macOS)
```bash
chmod +x start.sh
./start.sh
```

#### Option B: Direct Command
```bash
export $(cat .env | grep -v '^#' | xargs)
uvicorn app.main:app --host 0.0.0.0 --port 8761 --reload
```

#### Option C: Production with Gunicorn (Recommended)
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app \
  --bind 0.0.0.0:8761 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

#### Option D: Docker

```bash
# Build image
docker build -t eureka-discovery:latest .

# Run container
docker run -d \
  --name eureka-discovery \
  -p 8761:8761 \
  -e MONGODB_URL="mongodb://mongo:27017/eureka" \
  -e SERVER_HOST="0.0.0.0" \
  -e SERVER_PORT="8761" \
  eureka-discovery:latest
```

#### Option E: Docker Compose

```bash
docker-compose up -d
```

### 4. Verify Deployment

```bash
# Health check
curl http://localhost:8761/health

# Expected response:
{
  "status": "UP",
  "service": "eureka-discovery-service",
  "self_preservation_mode": {
    "enabled": false,
    "threshold_percentage": 85.0,
    "metrics": null
  }
}

# Service info
curl http://localhost:8761/info

# Metrics
curl http://localhost:8761/metrics | head -20
```

---

## Production Configuration

### 1. Tuning Cache Performance

For services with stable instance sets, increase cache TTL:

```python
# In app/services/CachedDiscoveryService.py
class CachedDiscoveryService(DiscoveryService):
    CACHE_TTL_SECONDS = 60  # Increased from 30s
```

For services with frequent changes, decrease TTL:

```python
    CACHE_TTL_SECONDS = 15  # Decreased from 30s
```

### 2. Adjusting Rate Limits

Based on expected traffic, update limits in `app/core/rate_limit.py`:

```python
# High-traffic deployment
registration_limiter = RateLimiter(
    default_capacity=200,      # Increased from 50
    default_refill_rate=20     # Increased from 5
)

heartbeat_limiter = RateLimiter(
    default_capacity=500,      # Increased from 200
    default_refill_rate=50     # Increased from 20
)

lookup_limiter = RateLimiter(
    default_capacity=5000,     # Increased from 1000
    default_refill_rate=500    # Increased from 100
)
```

### 3. Health Check Configuration

For services with slow health check endpoints:

```python
# In app/core/health_check.py
config = HealthCheckConfig(
    max_retries=5,              # More retries for unreliable networks
    timeout_seconds=10,         # Longer timeout
    backoff_factor=1.5,         # Less aggressive backoff
    initial_delay_seconds=2.0   # Longer initial delay
)
```

### 4. Self-Preservation Mode Threshold

For services with unreliable networks:

```python
# In app/core/self_preservation.py
class SelfPreservationMode:
    HEARTBEAT_RATE_THRESHOLD = 80.0  # More lenient (from 85%)
```

### 5. Logging Configuration

For debugging in production:

```env
# In .env file
LOG_LEVEL=DEBUG  # More verbose logging
```

Or update in code:

```python
# In app/main.py
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/discovery-service.log'),
        logging.StreamHandler()
    ]
)
```

---

## Monitoring & Observability

### 1. Prometheus Integration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'eureka-discovery'
    static_configs:
      - targets: ['localhost:8761']
    metrics_path: '/metrics'
```

Run Prometheus:

```bash
docker run -d \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### 2. Grafana Dashboard

Add Prometheus data source in Grafana:

```
URL: http://localhost:9090
```

Create dashboard with these queries:

```promql
# Active instances by status
eureka_active_instances

# Registration rate (per minute)
rate(eureka_registrations_total[1m])

# Cache hit rate
rate(eureka_cache_hits_total[5m]) / (rate(eureka_cache_hits_total[5m]) + rate(eureka_cache_misses_total[5m]))

# Request latency (p99)
histogram_quantile(0.99, eureka_request_duration_seconds_bucket)

# Self-preservation status
eureka_self_preservation_enabled
```

### 3. Key Metrics to Monitor

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| `eureka_active_instances` | < Expected | Investigate missing instances |
| `eureka_heartbeat_failures_total` | > 5% | Check client health |
| `eureka_evictions_total` | Spike | Possible network issues |
| `eureka_cache_misses_total` | > 50% | Check cache TTL |
| `eureka_self_preservation_enabled` | true | Network partition detected |
| `eureka_request_duration_seconds` | > 500ms | Database/performance issue |

---

## Scaling Considerations

### Horizontal Scaling

For high-traffic deployments, run multiple instances:

```bash
# Instance 1
SERVER_PORT=8761 ./start.sh

# Instance 2
SERVER_PORT=8762 ./start.sh

# Instance 3
SERVER_PORT=8763 ./start.sh
```

Place behind a load balancer:

```nginx
upstream eureka {
    server localhost:8761;
    server localhost:8762;
    server localhost:8763;
}

server {
    listen 80;
    location / {
        proxy_pass http://eureka;
    }
}
```

### MongoDB Optimization

Create indexes for better performance:

```javascript
// In MongoDB shell
db.service_instances.createIndex({ "instance_id": 1 })
db.service_instances.createIndex({ "app_name": 1 })
db.service_instances.createIndex({ "status": 1 })
db.service_instances.createIndex({ "last_heartbeat": 1 })
db.service_instances.createIndex({ "lease_expiration_time": 1 })

db.services.createIndex({ "name": 1 }, { unique: true })
```

---

## Troubleshooting

### High Memory Usage

**Symptoms**: Process using >500MB RAM

**Solutions**:
1. Reduce cache TTL: `CACHE_TTL_SECONDS = 15`
2. Clear cache periodically: `await cache.clear()`
3. Check for memory leaks in logs

### Cache Not Working

**Symptoms**: All lookups hitting database (cache misses 100%)

**Solutions**:
1. Check cache is initialized: `cache = get_cache()`
2. Verify TTL is appropriate
3. Check cache.get_size() in logs
4. Clear and restart: `await cache.clear()`

### Rate Limits Too Strict

**Symptoms**: Clients getting 429 Too Many Requests

**Solutions**:
1. Increase rate limit capacity
2. Check client is respecting backoff
3. Monitor `remaining_tokens` in rate limiter

### Self-Preservation Stuck Enabled

**Symptoms**: Eviction never runs, instances accumulate

**Solutions**:
1. Check heartbeat rate in `/self-preservation` endpoint
2. Verify network connectivity to instances
3. Lower threshold if needed
4. Check instance health check URLs

### High Latency on Lookups

**Symptoms**: Response time > 100ms

**Solutions**:
1. Increase cache TTL (reduce cache misses)
2. Check database performance
3. Monitor request histogram at `/metrics`
4. Check network latency to MongoDB

---

## Backup & Recovery

### Database Backup

```bash
# Backup MongoDB
mongodump --uri "mongodb://user:pass@host:port/eureka" \
  --out backup_$(date +%Y%m%d)

# Restore MongoDB
mongorestore --uri "mongodb://user:pass@host:port/eureka" \
  backup_20231226
```

### Configuration Backup

```bash
# Backup .env file
cp .env .env.backup.$(date +%Y%m%d)

# Backup custom configurations
cp app/core/rate_limit.py app/core/rate_limit.py.backup
cp app/core/caching.py app/core/caching.py.backup
```

---

## Update Procedure

### Updating to New Version

```bash
# 1. Backup current state
cp .env .env.backup
mongodump --uri "$MONGODB_URL" --out backup_$(date +%Y%m%d)

# 2. Pull latest changes
git pull origin main

# 3. Install updated dependencies
pip install -r requirements.txt --upgrade

# 4. Test with new version
python -m pytest tests/

# 5. Restart service
pkill -f "uvicorn app.main:app"
./start.sh
```

---

## Maintenance Tasks

### Daily
- Monitor metrics dashboard
- Check error logs
- Verify all instances are healthy

### Weekly
- Review cache hit rate (should be >70%)
- Check eviction count (should be <5/day)
- Analyze rate limit rejections

### Monthly
- Analyze traffic patterns
- Tune configuration if needed
- Review self-preservation activations
- Update dependencies if needed

---

## Performance Benchmarks

Expected performance on standard hardware (4 cores, 8GB RAM):

| Operation | Latency (p50) | Latency (p99) | Throughput |
|-----------|--------------|--------------|-----------|
| Lookup (cached) | <1ms | <5ms | 10,000+ req/s |
| Lookup (uncached) | 30ms | 100ms | 500+ req/s |
| Registration | 50ms | 150ms | 100+ req/s |
| Heartbeat | 20ms | 50ms | 1,000+ req/s |

With caching, typical throughput: **10,000+ req/s**

---

## Security Considerations

1. **Firewall Rules**: Only expose port 8761 to authorized services
2. **MongoDB Auth**: Use strong credentials in connection string
3. **Rate Limiting**: Protect against brute force registration
4. **Logging**: Don't log sensitive information
5. **Metrics**: Secure `/metrics` endpoint in production

Example nginx security config:

```nginx
location /metrics {
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    deny all;
}
```

---

## Support & Troubleshooting

### Common Issues

1. **Connection refused**: Check MongoDB is running and accessible
2. **Out of memory**: Reduce cache TTL or instance count
3. **Slow performance**: Check database indexes and network
4. **High evictions**: Check instance health and network

### Getting Help

1. Check logs: `tail -f logs/discovery-service.log`
2. Review metrics: `curl http://localhost:8761/metrics`
3. Check health: `curl http://localhost:8761/health`
4. Review documentation: `ENHANCEMENTS.md`, `ARCHITECTURE.md`
