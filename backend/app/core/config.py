"""
Configuration management for Indexing QA Observability Tool
Simplified version for compatibility
"""

import os
from typing import Optional, Dict, Any, List
from functools import lru_cache
from pydantic_settings import BaseSettings
from enum import Enum


class Environment(str, Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """Application settings with environment-specific configurations"""
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}
    
    # Environment Configuration
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    
    # Database Configuration
    database_url: str = "sqlite:///./indexing_qa.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    
    # Azure Storage Configuration
    azure_storage_connection_string: str = "UseDevelopmentStorage=true"
    azure_storage_container_reports: str = "reports"
    azure_storage_container_dead_letters: str = "dead-letters"
    azure_storage_container_golden_datasets: str = "golden-datasets"
    azure_storage_container_learning_results: str = "learning-results"
    
    # Azure Key Vault Configuration
    key_vault_url: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    
    # LLM Configuration
    openai_api_key: str = "your-openai-api-key-here"
    openai_model: str = "gpt-3.5-turbo"
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.1
    openai_rate_limit_requests_per_minute: int = 60
    
    anthropic_api_key: str = "your-anthropic-api-key-here"
    anthropic_model: str = "claude-3-sonnet-20240229"
    anthropic_max_tokens: int = 1000
    anthropic_rate_limit_requests_per_minute: int = 50
    
    # LLM Model Settings
    llm_model: str = "gpt-3.5-turbo"
    llm_max_tokens: int = 1000
    llm_temperature: float = 0.1
    
    # Quality Thresholds
    quality_pass_rate_threshold: float = 95.0
    quality_confidence_threshold: float = 0.8
    rules_engine_failure_rate_threshold: float = 10.0
    dead_letter_backlog_threshold: int = 100
    
    # Cost Management
    cost_budget_daily_limit: float = 100.0
    cost_budget_monthly_limit: float = 2000.0
    cost_alert_threshold_percentage: float = 80.0
    
    # Alert Configuration
    slack_webhook_url: Optional[str] = None
    slack_channel: str = "#indexing-qa-alerts"
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_recipients: List[str] = []
    alert_throttle_minutes: int = 30
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    api_rate_limit_requests: int = 100
    api_rate_limit_window: int = 60
    api_timeout: int = 300
    
    # Dashboard Configuration
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8501
    dashboard_page_size: int = 50
    dashboard_auto_refresh_seconds: int = 30
    
    # Rules Engine Configuration
    min_tag_count: int = 1
    max_tag_count: int = 20
    spam_threshold: float = 0.3
    stopword_threshold: float = 0.5
    rules_engine_batch_size: int = 1000
    rules_engine_max_workers: int = 4
    rules_stopwords_file: str = "stopwords.txt"
    rules_min_chunk_length: int = 10
    rules_max_chunk_length: int = 10000
    rules_max_tags_per_chunk: int = 20
    
    # LLM Judge Configuration
    enable_llm_validation: bool = True
    enable_async_processing: bool = True
    enable_alerts: bool = True
    llm_judge_batch_size: int = 10
    llm_judge_max_workers: int = 2
    llm_judge_retry_attempts: int = 3
    llm_judge_backoff_factor: float = 2.0
    llm_judge_pii_mask_enabled: bool = True
    llm_confidence_threshold: float = 0.6  # Threshold for LLM semantic validation
    
    # Feedback Loop Configuration
    feedback_learning_rate: float = 0.1
    feedback_min_samples_for_update: int = 10
    feedback_confidence_boost: float = 0.05
    feedback_golden_dataset_max_size: int = 10000
    
    # Retention and Cleanup
    data_retention_days: int = 90
    backup_retention_days: int = 30
    log_retention_days: int = 14
    
    # Performance and Monitoring
    performance_monitoring_enabled: bool = True
    metrics_collection_interval: int = 60
    health_check_interval: int = 300
    
    # Security
    api_key_header: str = "X-API-Key"
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3003,http://localhost:3004"
    cors_allow_credentials: bool = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_test(self) -> bool:
        """Check if running in test environment"""
        return self.environment == Environment.TEST
    
    @property
    def database_config(self) -> Dict[str, Any]:
        """Get database configuration dictionary"""
        return {
            "url": self.database_url,
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
            "pool_timeout": self.database_pool_timeout,
            "echo": self.debug and not self.is_production
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings() 