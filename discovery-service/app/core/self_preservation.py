"""
Self-Preservation Mode for Discovery Service
Stops evicting instances when heartbeat rate is too low
Equivalent to Netflix Eureka's self-preservation mode
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SelfPreservationMetrics:
    """Metrics for self-preservation monitoring"""
    
    total_expected_heartbeats: int
    total_received_heartbeats: int
    last_updated: datetime
    
    @property
    def heartbeat_rate(self) -> float:
        """Get current heartbeat rate as percentage"""
        if self.total_expected_heartbeats == 0:
            return 100.0
        return (self.total_received_heartbeats / self.total_expected_heartbeats) * 100


class SelfPreservationMode:
    """Manages self-preservation mode logic"""
    
    # Threshold: If heartbeat rate drops below this, enable self-preservation
    HEARTBEAT_RATE_THRESHOLD = 85.0  # 85%
    
    # Time window for calculating heartbeat rate
    METRICS_WINDOW_SECONDS = 60
    
    def __init__(self):
        self.enabled = False
        self.metrics: Optional[SelfPreservationMetrics] = None
        self.enabled_at: Optional[datetime] = None
        self.lease_renewal_interval = 30  # seconds
    
    def update_metrics(
        self,
        total_expected: int,
        total_received: int
    ):
        """Update heartbeat metrics"""
        self.metrics = SelfPreservationMetrics(
            total_expected_heartbeats=total_expected,
            total_received_heartbeats=total_received,
            last_updated=datetime.utcnow()
        )
        
        self._check_mode()
    
    def _check_mode(self):
        """Check if self-preservation should be enabled/disabled"""
        if not self.metrics:
            return
        
        heartbeat_rate = self.metrics.heartbeat_rate
        
        # Enable self-preservation if rate drops below threshold
        if heartbeat_rate < self.HEARTBEAT_RATE_THRESHOLD:
            if not self.enabled:
                self.enabled = True
                self.enabled_at = datetime.utcnow()
                logger.warning(
                    f"Self-preservation mode ENABLED. "
                    f"Heartbeat rate: {heartbeat_rate:.2f}% "
                    f"(threshold: {self.HEARTBEAT_RATE_THRESHOLD}%). "
                    f"Evictions will be disabled."
                )
        else:
            if self.enabled:
                self.enabled = False
                self.enabled_at = None
                logger.info(
                    f"Self-preservation mode DISABLED. "
                    f"Heartbeat rate: {heartbeat_rate:.2f}%. "
                    f"Evictions will resume."
                )
    
    def is_enabled(self) -> bool:
        """Check if self-preservation mode is currently enabled"""
        return self.enabled
    
    def get_status(self) -> dict:
        """Get self-preservation mode status"""
        status = {
            "enabled": self.enabled,
            "enabled_at": self.enabled_at.isoformat() if self.enabled_at else None,
            "threshold_percentage": self.HEARTBEAT_RATE_THRESHOLD,
            "metrics": None
        }
        
        if self.metrics:
            status["metrics"] = {
                "total_expected_heartbeats": self.metrics.total_expected_heartbeats,
                "total_received_heartbeats": self.metrics.total_received_heartbeats,
                "heartbeat_rate_percentage": round(self.metrics.heartbeat_rate, 2),
                "last_updated": self.metrics.last_updated.isoformat()
            }
        
        return status


# Global self-preservation mode instance
_self_preservation_mode: Optional[SelfPreservationMode] = None


def get_self_preservation_mode() -> SelfPreservationMode:
    """Get or create global self-preservation mode instance"""
    global _self_preservation_mode
    if _self_preservation_mode is None:
        _self_preservation_mode = SelfPreservationMode()
    return _self_preservation_mode
