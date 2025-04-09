"""
Service layer for pizza-related operations.
Handles business logic and agent selection.
"""
from enum import Enum
import logging
from opentelemetry import trace
from typing import Optional

from domains.pizza.models.messages import PizzaRequest, PizzaResponse, PizzaAgent
from domains.pizza.agents.pizza_agent_sk import SemanticKernelPizzaAgent
from domains.pizza.agents.pizza_agent import PizzaAgent as AzureAIPizzaAgent
from domains.pizza.agents.pizza_chat_sk import PizzaChatSK
from infra.errors import DomainError
from config import settings, BackendType

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class PizzaService:
    """Service for handling pizza-related operations."""
    
    def __init__(self, agent: PizzaAgent) -> None:
        """Initialize the PizzaService with a pre-created agent."""
        self.agent = agent
        
    @classmethod
    async def create(cls) -> "PizzaService":
        """
        Create and initialize a new PizzaService instance.
        
        Returns:
            PizzaService: A new service instance with the configured agent
            
        Raises:
            DomainError: If the configured backend type is invalid
        """
        agent = await cls._create_agent()
        return cls(agent=agent)
        
    @staticmethod
    async def _create_agent() -> PizzaAgent:
        """
        Create the appropriate agent based on configuration.
        
        Returns:
            PizzaAgent: An implementation of the PizzaAgent protocol
            
        Raises:
            DomainError: If the configured backend type is invalid
        """
        with tracer.start_as_current_span("pizza_service._create_agent") as span:
            span.set_attribute("backend_type", settings.backend_type)
            
            match settings.backend_type:
                case BackendType.SEMANTIC_KERNEL_AGENT:
                    logger.info("Initializing with Semantic Kernel Agent backend")
                    return await SemanticKernelPizzaAgent.create()
                case BackendType.SEMANTIC_KERNEL:
                    logger.info("Initializing with direct Semantic Kernel backend")
                    return PizzaChatSK()
                case BackendType.AZURE_AI_AGENT:
                    logger.info("Initializing with Azure AI Agent backend")
                    return await AzureAIPizzaAgent.create()
                case _:
                    raise DomainError(
                        detail=f"Invalid backend type: {settings.backend_type}",
                        title="Configuration Error"
                    )
        
    async def process_request(self, request: PizzaRequest) -> PizzaResponse:
        """
        Process a pizza-related request by delegating to the selected backend.
        
        Args:
            request: The PizzaRequest containing message and optional thread_id
            
        Returns:
            PizzaResponse: Response from the backend with conversation tracking info
            
        Raises:
            DomainError: If the backend processing fails
        """
        with tracer.start_as_current_span("pizza_service.process_request") as span:
            span.set_attribute("thread_id", str(request.thread_id))
            span.set_attribute("message_length", len(request.message))
            
            try:
                logger.info(f"Processing pizza request with thread_id: {request.thread_id}")
                response = await self.agent.process_message(request.message, request.thread_id)
                
                # Convert dict responses to PizzaResponse if needed
                if isinstance(response, dict):
                    if response["status"] == "error":
                        span.set_attribute("error", True)
                        span.set_attribute("error.message", response["message"])
                        raise DomainError(
                            detail=response["message"],
                            title="Pizza Processing Error"
                        )
                        
                    return PizzaResponse(
                        status=response["status"],
                        message=response["message"],
                        thread_id=response.get("thread_id"),
                        message_id=response.get("message_id")
                    )
                    
                span.set_attribute("response_length", len(response.message))
                return response
                
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                
                if isinstance(e, DomainError):
                    raise
                logger.error(f"Failed to process pizza request: {e}", exc_info=True)
                raise DomainError(
                    detail=str(e),
                    title="Pizza Processing Error"
                )