"""
Pizza agent implementation using Semantic Kernel with AzureAIAgent.
"""
import os
import logging
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgentThread, AzureAIAgent

from domains.pizza.models.messages import PizzaAgent, PizzaResponse
from config import settings

logger = logging.getLogger(__name__)

class SemanticKernelPizzaAgent:
    """
    Implementation of PizzaAgent using Semantic Kernel with AzureAIAgent.
    Handles agent initialization, thread management, and message processing.
    """
    
    def __init__(self, project_client: AIProjectClient, agent: AzureAIAgent) -> None:
        """Initialize with preconfigured client and agent."""
        self.project_client = project_client
        self.agent = agent

    @classmethod
    async def create(cls) -> "SemanticKernelPizzaAgent":
        """
        Create and initialize a new SemanticKernelPizzaAgent instance.
        
        Returns:
            SemanticKernelPizzaAgent: Initialized agent instance
        """
        credential = DefaultAzureCredential()
        project_client = AIProjectClient.from_connection_string(
            credential=credential,
            conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )
        
        try:
            logger.info(f"Initializing agent with ID: {settings.pizza_agent_id}")
            aif_agent = await project_client.agents.get_agent(
                agent_id=settings.pizza_agent_id
            )
            
            agent = AzureAIAgent(
                client=project_client,
                definition=aif_agent,
            )

            logger.info(f"Initialized agent with ID: {aif_agent.id}")
            return cls(project_client=project_client, agent=agent)

        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    async def process_message(self, message: str, thread_id: Optional[str] = None) -> PizzaResponse:
        """
        Process a message using the Semantic Kernel pizza agent.
        
        Args:
            message: The user's pizza-related query
            thread_id: Optional thread ID for maintaining conversation context
            
        Returns:
            PizzaResponse: Agent's response with conversation tracking info
        """
        try:
            # Create or reuse conversation thread
            thread = AzureAIAgentThread(
                client=self.project_client,
                thread_id=thread_id,
            )
            
            logger.info(f"Processing message with thread {thread_id}")
            response = await self.agent.get_response(messages=[message], thread=thread)
            logger.info("Received response")

            return PizzaResponse(
                status="success",
                message=response.content.content,
                thread_id=response.thread.id
            )
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return PizzaResponse(
                status="error",
                message=str(e),
                thread_id=thread_id
            )