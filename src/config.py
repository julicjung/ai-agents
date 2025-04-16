"""
Configuration settings for the application.
Handles loading environment variables and providing settings for the application.
Uses Pydantic for type-safe configuration management.
Ensures .env variables are loaded before any config parsing.
"""
from dotenv import load_dotenv
load_dotenv()
import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class BackendType(str, Enum):
    """Enum for different backend types that can process AI requests."""
    AZURE_AI_AGENT = "azure_ai_agent"          # Uses Azure AI Agent Service
    SEMANTIC_KERNEL = "semantic_kernel"         # Uses direct Semantic Kernel integration
    SEMANTIC_KERNEL_AGENT = "semantic_kernel_agent"  # Uses Semantic Kernel with Agent capabilities
    GROUP_CHAT_SK = "group_chat_sk"  # Uses Semantic Kernel group chat agent

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
        EnvironmentMode.PRODUCTION,
        description="Current environment mode (development/production)"
    )
    
    # AI Agent Settings
    pizza_agent_id: str = Field(
        "pizza-dough-agent-id",
        description="ID of the AI agent to use for pizza-related queries"
    )
    
    # Pizza Dough Agent IDs
    neapolitan_dough_agent: str = Field(
        "neapolitan-dough-agent",
        description="ID of the Neapolitan dough agent for pizza-related queries"
    )
    roman_dough_agent: str = Field(
        "roman-dough-agent",
        description="ID of the Roman dough agent for pizza-related queries"
    )
    dough_simplifier_agent: str = Field(
        "dough-simplifier-agent",
        description="ID of the dough simplifier agent for pizza-related queries"
    )
    
    # API Settings
    api_prefix: str = Field("/api", description="API endpoint prefix for all routes")
    
    # Health Check Settings
    health_check_token: str = Field(
        "vh7EBWcZq4kP9XmN2sYgT8JH3aRd6MuQ",
        description="Token used for authenticating health check requests"
    )
    
    # Backend Selection
    backend_type: BackendType = Field(
        BackendType.SEMANTIC_KERNEL_AGENT,
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

# Create settings instance by parsing environment variables
settings = Settings(
    environment=os.getenv("ENVIRONMENT", EnvironmentMode.PRODUCTION),
    api_prefix=os.getenv("API_PREFIX", "/api"),
    health_check_token=os.getenv("HEALTH_CHECK_TOKEN", "vh7EBWcZq4kP9XmN2sYgT8JH3aRd6MuQ"),
    backend_type=os.getenv("BACKEND_TYPE", BackendType.SEMANTIC_KERNEL_AGENT),
    enable_telemetry=os.getenv("ENABLE_TELEMETRY", "true").lower() == "true",
    azure_monitor_connection_string=os.getenv("AZURE_MONITOR_CONNECTION_STRING"),
    pizza_agent_id=os.getenv("PIZZA_AGENT_ID", "pizza-dough-agent-id"),
    neapolitan_dough_agent=os.getenv("NEAPOLITAN_DOUGH_AGENT", "neapolitan-dough-agent"),
    roman_dough_agent=os.getenv("ROMAN_DOUGH_AGENT", "roman-dough-agent"),
    dough_simplifier_agent=os.getenv("DOUGH_SIMPLIFIER_AGENT", "dough-simplifier-agent")
)