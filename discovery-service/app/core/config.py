"""
Core Configuration Module
Equivalent to Spring Boot @Configuration and @Value annotations
Maps application.properties settings to Pydantic BaseSettings
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application Configuration.
    Equivalent to Spring Boot application.properties
    """
    
    # Server Configuration
    server_port: int = 8761
    server_host: str = "0.0.0.0"
    
    # Application Details
    application_name: str = "discovery-service"
    application_version: str = "1.0.0"
    
    # Eureka Configuration
    eureka_instance_hostname: str = "localhost"
    eureka_instance_prefer_ip_address: bool = True
    eureka_client_register_with_eureka: bool = False
    eureka_client_fetch_registry: bool = False
    eureka_client_service_url_default_zone: str = "http://localhost:8761/eureka/"
    eureka_server_wait_time_in_ms_when_sync_empty: int = 5
    
    # MongoDB Configuration
    mongodb_url: str = "mongodb://timesmartui:timesmartui@ec2-23-20-18-226.compute-1.amazonaws.com/qa_timesmartai"
    mongodb_database: str = "qa_timesmartai"
    
    # Management/Actuator Configuration
    management_endpoints_web_exposure_include: str = "*"
    
    # Logging
    log_level: str = "INFO"
    
    # Security
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
