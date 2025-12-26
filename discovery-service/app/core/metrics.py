"""
Prometheus Metrics for Discovery Service
Tracks registrations, deregistrations, heartbeats, and instance counts
"""

from prometheus_client import Counter, Gauge, Histogram
import time

# Registration metrics
registrations_total = Counter(
    'eureka_registrations_total',
    'Total number of service instance registrations',
    ['app_name', 'status']
)

deregistrations_total = Counter(
    'eureka_deregistrations_total',
    'Total number of service instance deregistrations',
    ['app_name']
)

# Heartbeat metrics
heartbeats_total = Counter(
    'eureka_heartbeats_total',
    'Total number of heartbeat renewals received',
    ['app_name', 'status']
)

heartbeat_failures_total = Counter(
    'eureka_heartbeat_failures_total',
    'Total number of heartbeat renewal failures',
    ['app_name', 'reason']
)

# Instance metrics
active_instances = Gauge(
    'eureka_active_instances',
    'Current number of active service instances',
    ['app_name', 'status']
)

total_applications = Gauge(
    'eureka_total_applications',
    'Total number of registered applications'
)

# Eviction metrics
evictions_total = Counter(
    'eureka_evictions_total',
    'Total number of expired instances evicted',
    ['app_name']
)

# Request metrics
request_duration_seconds = Histogram(
    'eureka_request_duration_seconds',
    'Discovery service request duration in seconds',
    ['endpoint', 'method', 'status']
)

# Lookup metrics
lookup_duration_seconds = Histogram(
    'eureka_lookup_duration_seconds',
    'Service lookup duration in seconds',
    ['lookup_type']
)

cache_hits_total = Counter(
    'eureka_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'eureka_cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)


class MetricsTracker:
    """Helper class to track metrics with context managers"""
    
    @staticmethod
    def track_request(endpoint: str, method: str):
        """Context manager to track request duration"""
        class RequestTracker:
            def __init__(self, endpoint, method):
                self.endpoint = endpoint
                self.method = method
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                status = 'error' if exc_type else 'success'
                request_duration_seconds.labels(
                    endpoint=self.endpoint,
                    method=self.method,
                    status=status
                ).observe(duration)
        
        return RequestTracker(endpoint, method)
    
    @staticmethod
    def track_lookup(lookup_type: str):
        """Context manager to track lookup duration"""
        class LookupTracker:
            def __init__(self, lookup_type):
                self.lookup_type = lookup_type
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                lookup_duration_seconds.labels(
                    lookup_type=self.lookup_type
                ).observe(duration)
        
        return LookupTracker(lookup_type)
