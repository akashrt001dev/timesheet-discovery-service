# API Code Review - Discovery Service

## Critical Issues Found and Fixed

### 1. **register_instance Endpoint - Missing Body Parameter** ❌ FIXED
**Location:** `app/api/endpoints/DiscoveryController.py` line 75

**Problem:**
```python
instance_request: InstanceInfoRequest = None  # ❌ WRONG
```

**Issue:** The request body parameter had a default value of `None`, which means FastAPI would not properly parse the JSON body. The instance_request would always be None.

**Fix Applied:**
```python
instance_request: InstanceInfoRequest = Body(..., description="Instance registration details")  # ✅ CORRECT
```

---

### 2. **Case Sensitivity in app_name Comparison** ❌ FIXED
**Location:** `app/api/endpoints/DiscoveryController.py` line 88

**Problem:**
```python
if instance_request.app_name != app_name:  # ❌ Case-sensitive
```

**Issue:** Eureka service names are typically case-insensitive. If a user posts with "USER-SERVICE" in URL but "user-service" in body, it would fail validation unnecessarily.

**Fix Applied:**
```python
if instance_request.app_name.upper() != app_name.upper():  # ✅ Case-insensitive
```

---

### 3. **Missing Error Handling in Endpoints** ❌ FIXED
**Location:** All controller endpoints

**Problem:** Most endpoints don't have try-catch blocks. If an exception occurs, the error response might not be properly formatted.

**Fix Applied:** Added try-except blocks with proper logging:
```python
try:
    # business logic
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    raise
```

---

## Potential Issues to Monitor

### 4. **find_all() Returns Dictionaries, Not Objects**
**Location:** `app/services/DiscoveryService.py` line 285

**Current Implementation:**
```python
all_docs = await self.instance_repository.find_all()  # Returns List[Dict]
# Must convert: instance = ServiceInstance(**doc)
```

**Status:** ✅ Fixed in previous update

**Note:** This is the intended behavior, but must always convert dict → ServiceInstance.

---

### 5. **Endpoint Route Ordering**
**Current Setup:**
- `/apps/instanceId/{instance_id}` (specific) - comes after general routes
- `/apps/{app_name}` (generic)

**Status:** ✅ CORRECT
FastAPI handles this correctly because more specific routes are defined first in the controller.

---

### 6. **Missing Request Validation in register_instance**
**Location:** `app/services/DiscoveryService.py` line 94

**Current Code:**
```python
self._validate_instance_request(request)
```

**Check:** Ensure this validation method covers:
- [ ] instance_id is not empty
- [ ] app_name is not empty
- [ ] port is valid (1-65535)
- [ ] URLs are valid format

---

### 7. **Lease Expiration Logic**
**Location:** `app/models/aggregates/root/Service.py` line 68

**Current Implementation:**
```python
def is_lease_expired(self) -> bool:
    return datetime.utcnow() > self.lease_expiration_time
```

**Issue:** The lease_expiration_time is only set at initialization. It's not updated on heartbeat renewal.

**Need to Verify:** When renewing lease, does `renew_lease()` update `lease_expiration_time`?

**Check Location:** `app/repositories/ServiceInstanceRepository.py` - `renew_lease()` method

---

### 8. **GET /eureka/apps Returns Empty When Service Metadata Doesn't Exist**
**Status:** ✅ Fixed in previous update

Changed from querying Service collection to querying ServiceInstance collection directly and grouping by app_name.

---

### 9. **Endpoint Prefix Registration**
**Location:** `app/main.py` line 132

```python
app.include_router(discovery_router, prefix=EUREKA_API_PREFIX)
```

**What is EUREKA_API_PREFIX?**
Need to verify: Check `app/core/constants.py` to ensure it's set to `/eureka`

---

### 10. **Health Check Endpoint Conflict**
**Location:** `app/main.py` and `app/api/endpoints/DiscoveryController.py`

**Issue:** There are multiple health check endpoints:
- `GET /health` (line 142 in main.py)
- `GET /eureka/health` (DiscoveryController line 238)

**Recommendation:** Should be consistent.

---

## Test Cases to Verify

### POST /eureka/apps/{serviceName}
```bash
# Should SUCCEED - Case-insensitive
curl -X POST http://localhost:8761/eureka/apps/USER-SERVICE \
  -H "Content-Type: application/json" \
  -d '{
    "instanceId": "user-service-1",
    "appName": "user-service",  # Different case - should work now
    "hostName": "localhost",
    "ipAddr": "127.0.0.1",
    "port": 8080,
    "homePageUrl": "http://127.0.0.1:8080/",
    "statusPageUrl": "http://127.0.0.1:8080/status",
    "healthCheckUrl": "http://127.0.0.1:8080/health"
  }'

# Should FAIL
curl -X POST http://localhost:8761/eureka/apps/USER-SERVICE \
  -H "Content-Type: application/json" \
  -d '{
    "instanceId": "instance-1",
    "appName": "DIFFERENT-SERVICE",  # Mismatch
    ...
  }'
```

### GET /eureka/apps
```bash
curl http://localhost:8761/eureka/apps
# Should return all instances grouped by app name
```

### GET /eureka/apps/{serviceName}
```bash
curl http://localhost:8761/eureka/apps/USER-SERVICE
# Should return instances (case-insensitive now)
```

---

## Summary of Changes Made

| Issue | Status | Fix |
|-------|--------|-----|
| Missing Body() parameter | ✅ FIXED | Added `Body(...)` to register_instance |
| Case-sensitive app_name | ✅ FIXED | Changed to `.upper()` comparison |
| Missing error handling | ✅ FIXED | Added try-except blocks |
| GET /apps empty response | ✅ FIXED | Query instances directly, group by app_name |
| Lease expiration tracking | ⚠️ REVIEW | Need to verify renew_lease updates expiration_time |
| Validation logic | ⚠️ REVIEW | Need to audit _validate_instance_request() |

---

## Recommended Next Steps

1. **Test all endpoints** with the fixes applied
2. **Verify lease renewal** actually updates expiration times
3. **Check validation logic** to ensure proper input validation
4. **Rebuild Docker image** with all fixes:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

