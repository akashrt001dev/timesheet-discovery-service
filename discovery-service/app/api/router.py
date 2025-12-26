"""
Discovery API Router
Main router that aggregates all discovery-related endpoints
"""

from fastapi import APIRouter

discovery_router = APIRouter(prefix="/eureka", tags=["discovery"])
