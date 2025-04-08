"""
Configuration settings for the application.
Handles loading environment variables and providing settings for the application.
Uses Pydantic for type-safe configuration management.
"""
import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class BackendType(str, Enum):
    """Enum for different backend types that can process AI requests."""
    AZURE_AI_AGENT = "azure_ai_agent"          # Uses Azure AI Agent Service
    SEMANTIC_KERNEL = "semantic_kernel"         # Uses direct Semantic Kernel integration
    SEMANTIC_KERNEL_AGENT = "semantic_kernel_agent"  # Uses Semantic Kernel with Agent capabilities

class EnvironmentMode(str, Enum):
    """Enum for different environment modes."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class Settings(BaseModel):
    """
    Application settings loaded from environment variables.
    All settings are validated through Pydantic's type system.
    """
    # Environment Settings
    environment: EnvironmentMode = Field(
        EnvironmentMode.PRODUCTION,  # Changed from DEVELOPMENT to PRODUCTION
        description="Current environment mode (development/production)"
    )
    
    # AI Agent Settings
    pizza_agent_id: str = Field(
        "pizza-dough-agent-id",
        description="ID of the AI agent to use for pizza-related queries"
    )
    
    # API Settings
    api_prefix: str = Field("/api", description="API endpoint prefix for all routes")
    
    # Health Check Settings
    health_check_token: str = Field(
        "vh7EBWcZq4kP9XmN2sYgT8JH3aRd6MuQ",  # Hardcoded token as requested
        description="Token used for authenticating health check requests"
    )
    
    # Backend Selection
    backend_type: BackendType = Field(
        BackendType.AZURE_AI_AGENT,
        description="Determines which AI backend implementation to use"
    )
    
    # Telemetry Settings
    enable_telemetry: bool = Field(
        True, 
        description="Controls whether application telemetry is collected"
    )
    azure_monitor_connection_string: Optional[str] = Field(
        None, 
        description="Connection string for Azure Monitor telemetry collection"
    )

    class Config:
        """Pydantic model configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create settings instance by parsing environment variables
settings = Settings(
    environment=os.getenv("ENVIRONMENT", EnvironmentMode.PRODUCTION),  # Changed default to PRODUCTION
    api_prefix=os.getenv("API_PREFIX", "/api"),
    health_check_token=os.getenv("HEALTH_CHECK_TOKEN", "vh7EBWcZq4kP9XmN2sYgT8JH3aRd6MuQ"),
    backend_type=os.getenv("BACKEND_TYPE", BackendType.SEMANTIC_KERNEL_AGENT),
    enable_telemetry=os.getenv("ENABLE_TELEMETRY", "true").lower() == "true",
    azure_monitor_connection_string=os.getenv("AZURE_MONITOR_CONNECTION_STRING"),
    pizza_agent_id=os.getenv("PIZZA_AGENT_ID", "pizza-dough-agent-id")
)